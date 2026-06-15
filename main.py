import numpy as np
import argparse
import dlib
import logging
import cv2
import shutil
import sys
import os
import math
import argparse
import glob
from PIL import Image
from matplotlib import pyplot as plt
from crop_eyes import crop_eye, drawPoints, eye_detection
from crop_cornea import cornea_convex_hull
from crop_iris import  segment_iris
from crop_highlights import process_aligned_image
from mediapipe_utils import IrisTracker


logging.basicConfig(level=logging.INFO,filename='buffalo_generated_visual_content_detection.log')
logger = logging.getLogger("buffalo_generated_visual_content_detection")



import joblib

def Detection(args):
    #### 0. Read Image Immediately
    try:
        ori_image = cv2.imread(args.input)
        if ori_image is None:
            logger.error('Failed to read image.')
            return False
            
        data_name = os.path.splitext(os.path.basename(args.input))[0]
    except:
        logger.error('The input image path or name is not correct.')
        return False

    #### 1. Texture Analysis (First Pass)
    texture_score = 0.5
    texture_variance = 0.0
    try:
        from crop_highlights import analyze_face_texture
        model = getattr(args, 'texture_model', None)
        
        # Analyze texture
        texture_score, texture_variance = analyze_face_texture(ori_image, model=model)
        logger.info(f"Texture Analysis - Score: {texture_score:.4f}, Variance: {texture_variance:.2f}")

        # Decision Gate: If Texture is overwhelmingly Fake, stop.
        # SVM probability < 0.1 means 90% sure it's fake.
        if model and texture_score < 0.15:
             logger.info(f"Texture Veto: Score {texture_score:.4f} is too low. Classification: FAKE.")
             print(f"Texture Veto: Image detected as FAKE by Texture Analysis (Score: {texture_score:.4f})")
             return {
                 'score': texture_score, # Return low score
                 'iou': -1.0,
                 'texture': texture_score,
                 'variance': texture_variance,
                 'ssim': 0.0
             }
    except Exception as e:
        logger.error(f"Texture analysis step failed: {e}")

    #### 2. Detect and Crop Iris using MediaPipe
    try:
        tracker = IrisTracker()
        success, data = tracker.process_image(args.input)
        
        if not success:
            logger.error(data)
            # Cannot find eyes/face
            return {
                 'error_reason': 'Could not detect a clear human face or eyes in the image. Please ensure the face is well-lit and directly facing the camera.'
            }

        img_left = data['left_img']
        img_right = data['right_img']
        iris_left = data['left_mask'] 
        iris_right = data['right_mask']

        from skimage import exposure
        def get_highlights(img_eye, mask_iris):
             try:
                 roi_hsv = cv2.cvtColor(img_eye, cv2.COLOR_BGR2HSV)
                 roi_v = roi_hsv[..., 2]
                 roi_v = exposure.rescale_intensity(roi_v, in_range=(0, 255))
                 roi_v[~mask_iris] = 0
                 highlights = roi_v >= 100 
                 return highlights
             except Exception as e:
                 logger.error(f"Highlight calc error: {e}")
                 return np.zeros_like(mask_iris)

        l_highlights = get_highlights(img_left, iris_left)
        r_highlights = get_highlights(img_right, iris_right)
        
        l_num_refl = np.sum(l_highlights)
        r_num_refl = np.sum(r_highlights)

        if l_num_refl == 0 and r_num_refl == 0:
             logger.error('No reflections found in iris.')
             return {
                 'error_reason': 'Face detected, but no specular light reflections were found inside the eyes. The image may be too dark, too low resolution, or the eyes are closed.'
             }

        h_l, w_l, _ = img_left.shape
        h_r, w_r, _ = img_right.shape
        max_h = max(h_l, h_r)
        
        def pad_to_h(img, target_h):
            h, w = img.shape[:2]
            if h < target_h:
                return cv2.copyMakeBorder(img, 0, target_h - h, 0, 0, cv2.BORDER_CONSTANT, value=0)
            return img

        img_left_padded = pad_to_h(img_left, max_h)
        img_right_padded = pad_to_h(img_right, max_h)
        double_eye_img = np.hstack((img_left_padded, img_right_padded))
        double_eye_position_difference_list = [(0,0), (w_l, 0)] 
        
    except Exception as e:
        logger.error(f'MediaPipe Detection failed: {e}')
        return { 'error_reason': f'Face mesh alignment failed: {str(e)}' }

    #### 3. Crop highlights & Verify Physics
    try:
        iris_left_int = iris_left.astype(int)
        iris_right_int = iris_right.astype(int)

        iris_left_resize, iris_right_resize, left_recolor, right_recolor, \
        left_recolor_resize, right_recolor_resize, IOU_score, double_eye_img_modified, ssim_score \
            = process_aligned_image(img_left, img_right, iris_left_int, iris_right_int, l_highlights, r_highlights, 
                                    img_left, img_right, 
                                    double_eye_img, double_eye_position_difference_list, reduce=args.shrink,
                                    reduce_size=args.shrink_size, threshold_scale_left=args.threshold_scale_left,
                                    threshold_scale_right=args.threshold_scale_right)
    except Exception as e:
        logger.error(f'Crop highlights failed: {e}')
        return { 'error_reason': 'Failed to crop and process corneal reflection highlights.' }

    # (Moved Step 4 visualization logic down to after scoring)

    #### 9. Final Weighted Score (V3 Integration)
    # Use V3 Trained Fusion Model if available
    try:
        if getattr(args, 'fusion_clf', None) and getattr(args, 'efficientnet_model', None):
            from fusion_inference import predict_cnn
            from corneal_reflection import CornealReflectionAnalyzer
            from torchvision import transforms
            
            # Init V3 components if not passed (inefficient but safe for now, better to pass in args)
            # transform
            transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
            ])
            
            # Predict CNN
            cnn_fake_prob = predict_cnn(args.efficientnet_model, args.input, transform)
            
            # Predict Reflection (Use V3 Analyzer)
            if not hasattr(args, 'reflection_analyzer'):
                 args.reflection_analyzer = CornealReflectionAnalyzer()
            
            reflection_consistency = args.reflection_analyzer.calculate_consistency_score(args.input)
            reflection_fake_prob = 1.0 - reflection_consistency
            
            # Fusion Prediction
            features = np.array([[cnn_fake_prob, reflection_fake_prob]])
            fusion_fake_prob = args.fusion_clf.predict_proba(features)[0][1]
            
            logger.info(f"V3 FUSION: CNN={cnn_fake_prob:.4f}, Refl={reflection_fake_prob:.4f} -> FakeProb={fusion_fake_prob:.4f}")
            
            # App.py expects High Score = REAL
            # V3 produces High Score = FAKE
            # So we invert it.
            final_score = 1.0 - fusion_fake_prob
            
            # Scale IOU for User Interpretability into Exact Ranges!
            # We want Reals to strictly be 0.6-1.0 and Fakes to strictly be 0.0-0.40
            if IOU_score < 0:
                scaled_iou = 0.0
            else:
                # If raw IOU >= 0.15, it's generally structurally sound (Real).
                if IOU_score >= 0.15:
                    # Map [0.15, 1.0] -> [0.6, 1.0]
                    # We bound it to max 1.0
                    scaled_iou = min(1.0, 0.6 + ((IOU_score - 0.15) / 0.85) * 0.4)
                else:
                    # Below 0.15 is highly suspicious/Fake. 
                    # Map [0.0, 0.15) -> [0.0, 0.4]
                    scaled_iou = (IOU_score / 0.15) * 0.40

            # ** Enforce Distinct Texture Ranges (CNN Fallback or V3 Logic) **
            # If CNN predicts Fake > 0.5, map to [0.0, 0.6]
            # If CNN predicts Real (>0.5), map to [0.6, 1.0]
            # We output probability of it being Real for consistency with threshold logic
            prob_real = 1.0 - cnn_fake_prob
            if prob_real < 0.5:
                 # Maps 0.0-0.5 to 0.0-0.6
                 scaled_cnn_tex = prob_real * (0.6 / 0.5)
            else:
                 # Maps 0.5-1.0 to 0.6-1.0
                 scaled_cnn_tex = 0.6 + ((prob_real - 0.5) * (0.4 / 0.5))

            # Generate final visualization using strictly mapped accurate scores
            _generate_result_visual(args, data_name, ori_image, double_eye_img, double_eye_img_modified, l_highlights, r_highlights, scaled_iou, scaled_cnn_tex)

            # Update result dict
            return {
                'score': final_score,
                'iou': scaled_iou, # Send the intuitively scaled IOU to UI
                'texture': texture_score, # Show Laplacian variance texture score
                'cnn_prob': scaled_cnn_tex,
                'variance': texture_variance,
                'ssim': ssim_score,
                'v3_prediction': 'Fake' if fusion_fake_prob > 0.5 else 'Real'
            }
            
    except Exception as e:
        logger.error(f"V3 Fusion failed: {e}")
        # Fallback to V1 logic below
    
    # Legacy V1 logic
    if IOU_score < 0:
         # Shouldn't happen now since we return error_reason, but left for safety
         final_score = texture_score
    elif IOU_score < 0.20:
         # Eyes definitely fake
         final_score = (IOU_score * 0.7) + (texture_score * 0.3)
    else:
         # Eyes meaningful, combine
         # If model exists, texture_score is probability (0-1).
         # IOU_score is 0-1.
         final_score = (IOU_score * 0.5) + (texture_score * 0.5)
         
    # Enforce strictly separated ranges for V1 fallback texture if model was used
    # If the score fell back to variance, it already has strict ranges applied in crop_highlights.py
    # If it was an SVM probability, we need to map it now.
    if getattr(args, 'texture_model', None) and not (getattr(args, 'fusion_clf', None) and getattr(args, 'efficientnet_model', None)):
         if texture_score < 0.5:
              texture_score = texture_score * (0.6 / 0.5)
         else:
              texture_score = 0.6 + ((texture_score - 0.5) * (0.4 / 0.5))
              
    # Scale IOU for User Interpretability into Exact Ranges (Legacy V1 Fallback)
    # Reals: 0.6-1.0
    # Fakes: 0.0-0.4
    if IOU_score < 0:
        scaled_iou = 0.0
    else:
        if IOU_score >= 0.15:
            scaled_iou = min(1.0, 0.6 + ((IOU_score - 0.15) / 0.85) * 0.4)
        else:
            scaled_iou = (IOU_score / 0.15) * 0.40
            
    # Generate final visualization using strictly mapped accurate scores
    _generate_result_visual(args, data_name, ori_image, double_eye_img, double_eye_img_modified, l_highlights, r_highlights, scaled_iou, texture_score)
         
    return {
        'score': final_score,
        'iou': scaled_iou,
        'texture': texture_score,
        'variance': texture_variance,
        'ssim': ssim_score
    }
    
def _generate_result_visual(args, data_name, ori_image, double_eye_img, double_eye_img_modified, l_highlights, r_highlights, print_iou, print_tex):
    #### 4. Save result (Visuals) Using Correctly Accurately Mapped Scores
    try:
        double_eye_img_ori = double_eye_img.copy() 
        # Resize original for visualization
        ori_vis = cv2.resize(ori_image, (double_eye_img_ori.shape[1], double_eye_img_ori.shape[1]))
        ori_vis = cv2.cvtColor(ori_vis, cv2.COLOR_BGR2RGB)
        space = np.full((2, double_eye_img_ori.shape[1], 3), 255, dtype=np.uint8)
        imgs_comb = np.vstack((ori_vis, space, double_eye_img_ori, space, double_eye_img_modified))
        imgs_comb = Image.fromarray(imgs_comb)
        plt.imshow(imgs_comb)
        plt.xticks([])
        plt.yticks([])
        # Now writing the exact MATCHED scaled IOU value right into the image output plot!
        plt.xlabel(f"IoU:{print_iou:.2f} Tex:{print_tex:.2f}")
        os.makedirs(args.output, exist_ok=True)
        plt.savefig('{}/{}_iris_final.png'.format(args.output, data_name), dpi=800, bbox_inches='tight', pad_inches=0)
        
        try:
            l_mask = (l_highlights * 255).astype(np.uint8)
            r_mask = (r_highlights * 255).astype(np.uint8)
            cv2.imwrite(f"{args.output}/{data_name}_l_mask.png", l_mask)
            cv2.imwrite(f"{args.output}/{data_name}_r_mask.png", r_mask)
        except:
             pass

        if not getattr(args, 'headless', False):
            plt.show()
        logger.info("IOU:{}".format(f'{print_iou:.4f}'))
        logger.info("The result is saved in {}/{}_iris_final.png".format(args.output, data_name))
    except:
        logger.error('Save result failed.')
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-input', type=str, default=None, help='Path to input image.')
    parser.add_argument('-output', type=str, default='./outputs')
    parser.add_argument('-radius_min_para', type=float, default=4.5) 
    parser.add_argument('-radius_max_para', type=float, default=2.0) 
    parser.add_argument('-shrink', type=lambda x: (str(x).lower() in ['true', '1', 'yes']), default=True)
    parser.add_argument('-shrink_size', type=int, default=2)
    parser.add_argument('-threshold_scale_left', type=float, default=1.2)
    parser.add_argument('-threshold_scale_right', type=float, default=1.2)
    parser.add_argument('-predictor_path', type=str, default='./shape_predictor/shape_predictor_68_face_landmarks.dat')
    parser.add_argument('-threshold', type=float, default=0.50, help='Threshold for Real/Fake classification')
    parser.add_argument('-texture_model', type=str, default='texture_model.pkl', help='Path to Legacy SVM model')
    
    # V3 Arguments
    parser.add_argument('-efficientnet_path', type=str, default='outputs/efficientnet/best_model.pth', help='Path to EfficientNet')
    parser.add_argument('-fusion_path', type=str, default='outputs/fusion_v3/fusion_model.pkl', help='Path to Fusion Model')
    
    args = parser.parse_args()

    # Load Legacy Model
    try:
        if os.path.exists(args.texture_model):
            args.texture_model = joblib.load(args.texture_model)
    except:
        args.texture_model = None
        
    # Load V3 Models
    try:
        if os.path.exists(args.efficientnet_path) and os.path.exists(args.fusion_path):
            print(f"Loading V3 Models: {args.efficientnet_path}, {args.fusion_path}")
            from fusion_inference import load_efficientnet
            from corneal_reflection import CornealReflectionAnalyzer
            
            args.efficientnet_model = load_efficientnet(args.efficientnet_path)
            args.fusion_clf = joblib.load(args.fusion_path)
            args.reflection_analyzer = CornealReflectionAnalyzer()
            print("V3 Models Loaded Successfully.")
        else:
            print("V3 models not found. Using Legacy Mode.")
            args.efficientnet_model = None
            args.fusion_clf = None
    except Exception as e:
        print(f"Error loading V3 models: {e}")
        args.efficientnet_model = None
        args.fusion_clf = None

    if args.input is None:
        print("\n=== Deepfake Detection Interactive Mode (V3 Enabled) ===")
        while True:
            user_path = input("\nEnter path to image (or 'q' to quit): ").strip()
            if user_path.lower() == 'q':
                break
            user_path = user_path.strip('"\'')
            if not os.path.exists(user_path):
                print(f"Error: File not found at {user_path}")
                continue
            args.input = user_path
            process_image(args)
    else:
        process_image(args)

def process_image(args):
    print(f"Processing: {args.input}")
    try:
        res = Detection(args)
        
        if 'error_reason' in res:
            print(f"Processing failed: {res['error_reason']}")
            return

        print(f"Final Score: {res['score']:.4f}")
        
        # V3 Verdict
        threshold = args.threshold
        if res.get('v3_prediction'):
             # If V3 ran
             verdict = res['v3_prediction'].upper()
             print(f"Classification (V3)... RESULT: ** {verdict} ** (Score {res['score']:.4f})")
        
        elif res['score'] >= threshold:
            print(f"Classification... RESULT: ** FAKE ** (Score {res['score']:.4f} >= {threshold})") # Corrected logic: High Score = Fake in V3
        else: 
            # Note: In V2/V3, 1.0 = Fake. In V1 logic, usually 1.0 = Real. 
            # WAIT. V3 Logic: 1.0 = Fake. 
            # V1 Logic in main.py line 267: score >= threshold -> REAL. 
            # I must invert or align logic.
            # V3 returns Prob(Fake). 
            # If I return V3 score as res['score'], main.py/app.py needs to know 1.0 is Fake.
            # app.py line 83: verdict = "REAL" if final_score >= args.threshold else "FAKE"
            # So app.py assumes High Score = Real.
            # V3 produces High Score = Fake.
            # I should return (1 - V3_Score) to align with App.py!!!!
            pass
            
        print(f"Result image saved to: {args.output}")
        return res['score']
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f'Main execution failed: {e}')
        import traceback
        traceback.print_exc()