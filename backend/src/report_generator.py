import os
import datetime
from fpdf import FPDF

class ForensicPDF(FPDF):
    def header(self):
        # Draw tech border/frame
        self.set_draw_color(99, 102, 241) # Neon Indigo
        self.set_line_width(1.5)
        self.rect(5, 5, 200, 287)
        
        # Header banner
        self.set_fill_color(17, 24, 39) # Dark gray background
        self.rect(5, 5, 200, 30, 'F')
        
        self.set_font('helvetica', 'B', 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 15, "AURAEYE FORENSICS", border=0, ln=1, align='C')
        
        self.set_font('helvetica', 'I', 10)
        self.set_text_color(129, 140, 248) # Indigo light
        self.cell(0, 5, "Physics-Guided Eye Specular Reflection Deepfake Analysis Report", border=0, ln=1, align='C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(156, 163, 175)
        self.cell(0, 10, f"Page {self.page_no()} | AuraEye Forensics Audit System", border=0, align='C')


class ReportGenerator:
    def __init__(self, reports_dir=None):
        if reports_dir is None:
            self.reports_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                'reports'
            )
        else:
            self.reports_dir = reports_dir
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate_pdf_report(self, user_name, user_email, record_id, metrics, image_path=None):
        """
        Generates a professional multi-page forensic PDF report containing metadata, images, and scores.
        """
        pdf = ForensicPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # --- PAGE 1: AUDIT & VERDICT INFORMATION ---
        pdf.add_page()
        pdf.set_left_margin(15)
        pdf.set_right_margin(15)
        pdf.set_text_color(17, 24, 39)
        pdf.ln(5)

        # 1. Audit Metadata Block
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 8, "AUDIT INFORMATION", border="B", ln=1)
        pdf.ln(2)
        
        pdf.set_font('helvetica', '', 10)
        col_w = 45
        
        pdf.cell(col_w, 6, "Report Identifier:", 0, 0)
        pdf.set_font('helvetica', 'B', 10)
        pdf.cell(0, 6, f"AE-AUDIT-{record_id:06d}", 0, 1)
        
        pdf.set_font('helvetica', '', 10)
        pdf.cell(col_w, 6, "Auditor Name:", 0, 0)
        pdf.cell(0, 6, str(user_name), 0, 1)
        
        pdf.cell(col_w, 6, "Auditor Email:", 0, 0)
        pdf.cell(0, 6, str(user_email), 0, 1)
        
        pdf.cell(col_w, 6, "Analysis Date/Time:", 0, 0)
        pdf.cell(0, 6, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0, 1)
        
        pdf.cell(col_w, 6, "Audited Media Name:", 0, 0)
        pdf.cell(0, 6, metrics["media_name"], 0, 1)
        
        pdf.ln(4)

        # 2. Final Prediction Verdict Block
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 8, "FORENSIC CLASSIFICATION VERDICT", border="B", ln=1)
        pdf.ln(3)
        
        verdict = metrics["result"]
        conf = metrics["confidence"]
        trust = metrics["trust_score"]
        risk = metrics["risk_level"]
        
        pdf.set_font('helvetica', 'B', 14)
        if verdict == "REAL":
            pdf.set_text_color(16, 185, 129) # Neon Green
            pdf.cell(0, 8, f"RESULT: REAL (Authentic Portrait)", 0, 1)
        else:
            pdf.set_text_color(239, 68, 68) # Red
            pdf.cell(0, 8, f"RESULT: DEEPFAKE (Generative/Edited Face)", 0, 1)
            
        pdf.set_text_color(17, 24, 39)
        pdf.set_font('helvetica', '', 11)
        pdf.cell(col_w, 6, "Confidence Score:", 0, 0)
        pdf.cell(0, 6, f"{conf:.2f}%", 0, 1)
        
        pdf.cell(col_w, 6, "Trust Score:", 0, 0)
        pdf.cell(0, 6, f"{trust} / 100", 0, 1)
        
        pdf.cell(col_w, 6, "Risk Assessment:", 0, 0)
        pdf.cell(0, 6, risk, 0, 1)
        
        pdf.ln(4)

        # 3. MediaPipe Landmark Alignment Coordinates
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 8, "LANDMARK PREPROCESSING", border="B", ln=1)
        pdf.ln(2)
        
        pdf.set_font('helvetica', '', 10)
        pdf.cell(col_w, 6, "Face Box Coordinates:", 0, 0)
        pdf.cell(0, 6, metrics["face_coords"], 0, 1)
        
        pdf.cell(col_w, 6, "Face Alignment Conf:", 0, 0)
        pdf.cell(0, 6, f"{metrics['face_confidence']:.4f}", 0, 1)
        
        pdf.ln(6)

        # 4. Embedded Visualizations (Face Detection and Mesh)
        # Find absolute paths of visuals
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        results_dir = os.path.join(backend_dir, 'static', 'results')
        
        face_img_path = os.path.join(results_dir, os.path.basename(metrics["visuals"]["face_url"]))
        mesh_img_path = os.path.join(results_dir, os.path.basename(metrics["visuals"]["mesh_url"]))
        
        # Display images side-by-side if they exist
        pdf.set_font('helvetica', 'B', 11)
        pdf.cell(90, 6, "Primary Face Detection Crop", 0, 0, 'C')
        pdf.cell(90, 6, "Ocular Mesh Landmarks", 0, 1, 'C')
        pdf.ln(2)
        
        y_pos = pdf.get_y()
        if os.path.exists(face_img_path):
            pdf.image(face_img_path, x=15, y=y_pos, w=85, h=85)
        else:
            pdf.rect(15, y_pos, 85, 85)
            pdf.text(35, y_pos + 40, "[Face Detection Visual]")
            
        if os.path.exists(mesh_img_path):
            pdf.image(mesh_img_path, x=110, y=y_pos, w=85, h=85)
        else:
            pdf.rect(110, y_pos, 85, 85)
            pdf.text(130, y_pos + 40, "[Ocular Mesh Visual]")
            
        # Move pointer past the images
        pdf.set_y(y_pos + 90)

        # --- PAGE 2: OCULAR BIOMETRICS & PHYSICS ANALYSIS ---
        pdf.add_page()
        pdf.ln(5)

        # 5. Detail Specular Reflection Metrics Table
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 8, "CORNEAL SPECULAR HIGHLIGHT EXTRACTION", border="B", ln=1)
        pdf.ln(4)
        
        # Headers
        pdf.set_font('helvetica', 'B', 10)
        pdf.set_fill_color(243, 244, 246)
        pdf.cell(60, 8, "Ocular Specular Metric", 1, 0, 'C', True)
        pdf.cell(60, 8, "Left Eye Reflection", 1, 0, 'C', True)
        pdf.cell(60, 8, "Right Eye Reflection", 1, 1, 'C', True)
        
        # Rows
        pdf.set_font('helvetica', '', 10)
        pdf.cell(60, 8, "Centroid Position (X, Y)", 1, 0, 'C')
        l_pos = metrics["blobs_details"]["left"]["position"]
        r_pos = metrics["blobs_details"]["right"]["position"]
        pdf.cell(60, 8, f"({l_pos[0]:.1f}, {l_pos[1]:.1f})", 1, 0, 'C')
        pdf.cell(60, 8, f"({r_pos[0]:.1f}, {r_pos[1]:.1f})", 1, 1, 'C')
        
        pdf.cell(60, 8, "Reflection Pixel Area", 1, 0, 'C')
        pdf.cell(60, 8, f"{metrics['blobs_details']['left']['area']:.1f} px", 1, 0, 'C')
        pdf.cell(60, 8, f"{metrics['blobs_details']['right']['area']:.1f} px", 1, 1, 'C')
        
        pdf.cell(60, 8, "Reflection Brightness (0-255)", 1, 0, 'C')
        pdf.cell(60, 8, f"{metrics['blobs_details']['left']['brightness']:.2f}", 1, 0, 'C')
        pdf.cell(60, 8, f"{metrics['blobs_details']['right']['brightness']:.2f}", 1, 1, 'C')
        
        pdf.ln(6)

        # 6. Embedded Specular Comparison Binarization
        comparison_img_path = os.path.join(results_dir, os.path.basename(metrics["visuals"]["comparison_url"]))
        
        pdf.set_font('helvetica', 'B', 11)
        pdf.cell(0, 6, "Isolated Corneal Highlight Comparison (Left / Right Aligned)", 0, 1, 'C')
        pdf.ln(2)
        
        y_pos_comp = pdf.get_y()
        if os.path.exists(comparison_img_path):
            # Maintain aspect ratio for side-by-side eyes comparison
            pdf.image(comparison_img_path, x=45, y=y_pos_comp, w=120, h=40)
            pdf.set_y(y_pos_comp + 45)
        else:
            pdf.rect(45, y_pos_comp, 120, 40)
            pdf.text(80, y_pos_comp + 20, "[Corneal Highlight Overlay Visual]")
            pdf.set_y(y_pos_comp + 45)

        # 7. Combined Physics Symmetry Metrics
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 8, "OCULAR FORENSIC INDICES & TEXTURE", border="B", ln=1)
        pdf.ln(2)
        
        pdf.set_font('helvetica', '', 10)
        # Texture Authenticity Score
        pdf.cell(75, 6, "Texture Authenticity Score:", 0, 0)
        pdf.set_font('helvetica', 'B', 10)
        pdf.cell(30, 6, f"{metrics.get('texture_score', 0.0):.4f}", 0, 1)
        pdf.set_font('helvetica', '', 10)
        
        pdf.cell(75, 6, "Reflection Symmetry Index (RSI):", 0, 0)
        pdf.cell(30, 6, f"{metrics['rsi']:.4f}", 0, 1)
        
        pdf.cell(75, 6, "Reflection Consistency Score (CRCS):", 0, 0)
        pdf.cell(30, 6, f"{metrics['crcs']:.2f} / 100", 0, 1)
        
        pdf.cell(75, 6, "Structural Similarity (SSIM):", 0, 0)
        pdf.cell(30, 6, f"{metrics['ssim']:.4f}", 0, 1)
        
        pdf.ln(4)

        # 8. Explainable AI Reason Checklist Block
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 8, "EXPLAINABLE AI (XAI) DIAGNOSTIC LOG", border="B", ln=1)
        pdf.ln(3)
        
        pdf.set_font('helvetica', '', 10)
        reasons = metrics.get("reasons", [])
        
        if not reasons:
            pdf.set_text_color(16, 185, 129)
            pdf.cell(0, 6, "[Passed] Specular reflection patterns are symmetric and physically consistent.", 0, 1)
        else:
            pdf.set_text_color(220, 38, 38)
            for r in reasons:
                pdf.cell(0, 6, f"- [Failed] {r}", 0, 1)
                
        pdf.set_text_color(17, 24, 39)
        pdf.ln(5)

        # Save report PDF
        filename = f"report_audit_{record_id:06d}.pdf"
        output_path = os.path.join(self.reports_dir, filename)
        pdf.output(output_path)
        
        return f"/static/reports/{filename}"
