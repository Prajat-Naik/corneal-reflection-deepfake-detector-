import React, { useState } from 'react';
import axios from 'axios';
import Sidebar from '../components/Sidebar';
import { 
  UploadCloud, FileImage, ShieldCheck, ShieldAlert, 
  UserCheck, Eye, Sparkles, RefreshCw, Download, 
  HelpCircle, GitCommit, Settings, ChevronRight
} from 'lucide-react';

const API_URL = 'http://127.0.0.1:5000/api';
const BASE_URL = 'http://127.0.0.1:5000';

function Workspace() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [activeTab, setActiveTab] = useState('summary');
  const [error, setError] = useState('');

  const loadingSteps = [
    "Reading media stream metadata...",
    "Running MediaPipe Face Detector...",
    "Aligning 3D face mesh coordinates...",
    "Cropping left and right corneal specular irises...",
    "Running Yen specularity extraction & adaptive thresholding...",
    "Evaluating Reflection Symmetry Index (RSI)...",
    "Calculating Corneal Reflection Consistency Score (CRCS)...",
    "Formulating Structural Similarity (SSIM) and Trust Scores..."
  ];

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setError('');
    const droppedFile = e.dataTransfer.files[0];
    validateAndSetFile(droppedFile);
  };

  const handleFileChange = (e) => {
    setError('');
    const selectedFile = e.target.files[0];
    validateAndSetFile(selectedFile);
  };

  const validateAndSetFile = (fileObj) => {
    if (!fileObj) return;
    const allowed = ['image/jpeg', 'image/jpg', 'image/png'];
    if (!allowed.includes(fileObj.type)) {
      setError("Unsupported file format. Please upload JPG, JPEG, or PNG.");
      return;
    }
    // Max 10MB
    if (fileObj.size > 10 * 1024 * 1024) {
      setError("File is too large. Max size allowed is 10MB.");
      return;
    }
    setFile(fileObj);
    setPreview(URL.createObjectURL(fileObj));
    setAnalysisResult(null);
  };

  const triggerAnalysis = async () => {
    if (!file) return;
    setError('');
    setLoading(true);
    setLoadingStep(0);

    // Simulate step loader increments
    const stepInterval = setInterval(() => {
      setLoadingStep(prev => {
        if (prev < loadingSteps.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 1200);

    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API_URL}/analyze`, formData, {
        headers: { 
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`
        }
      });

      setAnalysisResult(response.data);
      setActiveTab('summary');
    } catch (err) {
      setError(err.response?.data?.message || 'Forensic analysis failed to compute.');
    } finally {
      clearInterval(stepInterval);
      setLoading(false);
    }
  };

  const getRiskColor = (risk) => {
    if (risk === "Trustworthy") return "text-emerald-400 bg-emerald-500/10 border-emerald-500/25";
    if (risk === "Medium Risk") return "text-yellow-400 bg-yellow-500/10 border-yellow-500/25";
    return "text-red-400 bg-red-500/10 border-red-500/25";
  };

  return (
    <div className="min-h-screen pl-64 bg-cyber-dark text-slate-100">
      <Sidebar />
      <main className="p-8 max-w-7xl mx-auto space-y-8">
        
        {/* Header Title */}
        <div className="flex justify-between items-center border-b border-slate-800 pb-5">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white">Forensic Inspection Workspace</h1>
            <p className="text-slate-400 text-sm mt-1">Upload portrait media files to analyze cornealSpecularity geometries and skin texture anomalies.</p>
          </div>
          {analysisResult && (
            <button
              onClick={() => {
                setFile(null);
                setPreview('');
                setAnalysisResult(null);
              }}
              className="border border-slate-800 hover:border-slate-700 bg-slate-900/30 text-slate-300 hover:text-white px-4 py-2 rounded-lg text-sm flex items-center gap-2 transition-all"
            >
              <RefreshCw className="w-4 h-4" />
              Reset Workspace
            </button>
          )}
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-200 text-sm p-4 rounded-xl">
            {error}
          </div>
        )}

        {/* Upload State / Landing View */}
        {!analysisResult && !loading && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
            {/* Left side: upload zone */}
            <div 
              onDragOver={handleDrag}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              className="bg-slate-900/40 border-2 border-dashed border-slate-800 hover:border-indigo-500/40 rounded-2xl p-10 flex flex-col items-center justify-center text-center cursor-pointer transition-all min-h-[400px]"
            >
              <input
                id="file-upload"
                type="file"
                className="hidden"
                accept=".jpg,.jpeg,.png"
                onChange={handleFileChange}
              />
              <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center justify-center">
                <div className="w-20 h-20 bg-indigo-500/10 border border-indigo-500/20 rounded-2xl flex items-center justify-center text-indigo-400 mb-6 shadow-inner">
                  <UploadCloud className="w-10 h-10" />
                </div>
                <h3 className="text-lg font-bold text-white mb-2">Drag & Drop Forensic Media</h3>
                <p className="text-slate-500 text-sm mb-4 max-w-xs">Supports JPG, JPEG, and PNG formats up to 10MB</p>
                <span className="bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-lg text-xs font-semibold shadow-lg shadow-indigo-650/15 transition-all">
                  Browse Files
                </span>
              </label>
            </div>

            {/* Right side: Preview card */}
            <div className="bg-slate-900/30 border border-slate-800 rounded-2xl p-6 min-h-[400px] flex flex-col items-center justify-center relative overflow-hidden">
              {preview ? (
                <div className="w-full flex flex-col items-center gap-6">
                  <div className="relative border border-slate-800 rounded-xl overflow-hidden max-h-[300px] max-w-full flex items-center justify-center shadow-lg">
                    <img src={preview} alt="Upload Preview" className="object-contain max-h-[300px] max-w-full" />
                  </div>
                  <div className="text-center">
                    <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">File Metadata</p>
                    <p className="text-white text-sm font-semibold mt-1 font-mono">{file.name}</p>
                    <p className="text-slate-400 text-xs mt-1">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                  </div>
                  <button
                    onClick={triggerAnalysis}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-8 py-3 rounded-lg text-sm shadow-xl shadow-indigo-650/15 flex items-center gap-2 transition-all mt-2"
                  >
                    <Sparkles className="w-4 h-4" />
                    Initialize AI Forensic Analysis
                  </button>
                </div>
              ) : (
                <div className="flex flex-col items-center text-slate-500">
                  <FileImage className="w-16 h-16 opacity-30 mb-4" />
                  <p className="text-sm">Image preview window will render here</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Loading Steps Screen */}
        {loading && (
          <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-12 flex flex-col items-center justify-center text-center backdrop-blur-md min-h-[450px] relative overflow-hidden">
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-indigo-500/5 rounded-full blur-3xl -z-10 animate-pulse"></div>
            
            <div className="w-16 h-16 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mb-8"></div>
            
            <h3 className="text-xl font-bold text-white mb-2">Analyzing specularity symmetry logs</h3>
            <p className="text-indigo-400 font-semibold text-sm max-w-md animate-pulse">
              {loadingSteps[loadingStep]}
            </p>
            <div className="w-64 bg-slate-950 border border-slate-850 h-2 rounded-full overflow-hidden mt-6 relative">
              <div 
                className="bg-indigo-500 h-full transition-all duration-1000 ease-out"
                style={{ width: `${((loadingStep + 1) / loadingSteps.length) * 100}%` }}
              ></div>
            </div>
            <p className="text-slate-500 text-xs mt-3">Executing MCA Research Algorithms v2.6</p>
          </div>
        )}

        {/* Forensic Results View (Tabbed dashboard) */}
        {analysisResult && !loading && (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 items-start">
            {/* Sidebar Tab Options */}
            <div className="lg:col-span-1 bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden backdrop-blur-sm">
              <div className="p-4 bg-slate-950/20 border-b border-slate-850">
                <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Analysis Sections</p>
              </div>
              <div className="flex flex-col">
                <button
                  onClick={() => setActiveTab('summary')}
                  className={`flex items-center gap-3 px-4 py-3 text-sm font-semibold transition-all text-left ${activeTab === 'summary' ? 'bg-indigo-600/10 text-indigo-400 border-l-4 border-indigo-500' : 'text-slate-400 hover:bg-slate-800/30 hover:text-slate-200'}`}
                >
                  <ShieldCheck className="w-4 h-4" />
                  Trust Summary
                </button>
                <button
                  onClick={() => setActiveTab('face')}
                  className={`flex items-center gap-3 px-4 py-3 text-sm font-semibold transition-all text-left ${activeTab === 'face' ? 'bg-indigo-600/10 text-indigo-400 border-l-4 border-indigo-500' : 'text-slate-400 hover:bg-slate-800/30 hover:text-slate-200'}`}
                >
                  <UserCheck className="w-4 h-4" />
                  Face Detection
                </button>
                <button
                  onClick={() => setActiveTab('eyes')}
                  className={`flex items-center gap-3 px-4 py-3 text-sm font-semibold transition-all text-left ${activeTab === 'eyes' ? 'bg-indigo-600/10 text-indigo-400 border-l-4 border-indigo-500' : 'text-slate-400 hover:bg-slate-800/30 hover:text-slate-200'}`}
                >
                  <Eye className="w-4 h-4" />
                  Eye Localization
                </button>
                <button
                  onClick={() => setActiveTab('reflection')}
                  className={`flex items-center gap-3 px-4 py-3 text-sm font-semibold transition-all text-left ${activeTab === 'reflection' ? 'bg-indigo-600/10 text-indigo-400 border-l-4 border-indigo-500' : 'text-slate-400 hover:bg-slate-800/30 hover:text-slate-200'}`}
                >
                  <Eye className="w-4 h-4" />
                  Specular Blobs
                </button>
                <button
                  onClick={() => setActiveTab('metrics')}
                  className={`flex items-center gap-3 px-4 py-3 text-sm font-semibold transition-all text-left ${activeTab === 'metrics' ? 'bg-indigo-600/10 text-indigo-400 border-l-4 border-indigo-500' : 'text-slate-400 hover:bg-slate-800/30 hover:text-slate-200'}`}
                >
                  <GitCommit className="w-4 h-4" />
                  Symmetry Indices
                </button>
                <button
                  onClick={() => setActiveTab('visual')}
                  className={`flex items-center gap-3 px-4 py-3 text-sm font-semibold transition-all text-left ${activeTab === 'visual' ? 'bg-indigo-600/10 text-indigo-400 border-l-4 border-indigo-500' : 'text-slate-400 hover:bg-slate-800/30 hover:text-slate-200'}`}
                >
                  <HelpCircle className="w-4 h-4" />
                  Visual Comparison
                </button>
              </div>
            </div>

            {/* Content Display Panels */}
            <div className="lg:col-span-3 bg-slate-900/30 border border-slate-800 rounded-2xl backdrop-blur-sm p-8 min-h-[450px]">
              
              {/* SUMMARY TAB */}
              {activeTab === 'summary' && (
                <div className="space-y-8">
                  {/* Verdict and trust metrics */}
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 bg-slate-950/20 border border-slate-800 p-6 rounded-xl">
                    <div className="space-y-2">
                      <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Classification Result</p>
                      {analysisResult.result === 'REAL' ? (
                        <h2 className="text-3xl font-extrabold text-emerald-400 flex items-center gap-2">
                          <ShieldCheck className="w-8 h-8 text-emerald-400" />
                          REAL
                        </h2>
                      ) : (
                        <h2 className="text-3xl font-extrabold text-red-500 flex items-center gap-2">
                          <ShieldAlert className="w-8 h-8 text-red-500" />
                          DEEPFAKE
                        </h2>
                      )}
                      <p className="text-slate-400 text-sm">Forensic confidence score: <span className="font-bold text-white">{analysisResult.confidence.toFixed(2)}%</span></p>
                    </div>

                    <div className="flex items-center gap-4">
                      {/* Trust Score Radial Indicator */}
                      <div className="relative w-20 h-20 flex items-center justify-center border-4 border-indigo-500/20 rounded-full">
                        <span className="text-2xl font-black text-white">{analysisResult.trust_score}</span>
                        <div className="absolute inset-0 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin-slow opacity-60"></div>
                      </div>
                      <div>
                        <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Trust Score</p>
                        <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-bold border mt-1 ${getRiskColor(analysisResult.risk_level)}`}>
                          {analysisResult.risk_level}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Explainable AI reasoning log checklist */}
                  <div className="space-y-4">
                    <h3 className="text-white font-bold text-lg">Explainable AI (XAI) Diagnostic Log</h3>
                    <div className="space-y-2">
                      <div className="flex items-center gap-3 bg-slate-950/10 p-3 rounded-lg">
                        <span className={`w-2.5 h-2.5 rounded-full ${analysisResult.reasons.includes("Reflection Position Mismatch detected") ? 'bg-red-500 shadow-lg shadow-red-500/30' : 'bg-emerald-500'}`}></span>
                        <p className="text-sm">Specular Highlight Position coordinates comparison</p>
                      </div>
                      <div className="flex items-center gap-3 bg-slate-950/10 p-3 rounded-lg">
                        <span className={`w-2.5 h-2.5 rounded-full ${analysisResult.reasons.includes("Reflection Brightness Difference detected") ? 'bg-red-500 shadow-lg shadow-red-500/30' : 'bg-emerald-500'}`}></span>
                        <p className="text-sm">Adaptive specularity brightness mismatch check</p>
                      </div>
                      <div className="flex items-center gap-3 bg-slate-950/10 p-3 rounded-lg">
                        <span className={`w-2.5 h-2.5 rounded-full ${analysisResult.reasons.includes("Low Reflection Symmetry Index (RSI)") ? 'bg-red-500 shadow-lg shadow-red-500/30' : 'bg-emerald-500'}`}></span>
                        <p className="text-sm">Reflection Symmetry Index (RSI) bounds validation</p>
                      </div>
                      <div className="flex items-center gap-3 bg-slate-950/10 p-3 rounded-lg">
                        <span className={`w-2.5 h-2.5 rounded-full ${analysisResult.reasons.includes("Low Structural Similarity Score (SSIM)") ? 'bg-red-500 shadow-lg shadow-red-500/30' : 'bg-emerald-500'}`}></span>
                        <p className="text-sm">Structural Similarity Index (SSIM) alignment check</p>
                      </div>
                    </div>
                  </div>

                  {/* Explanations text block & download button */}
                  <div className="space-y-4 border-t border-slate-800 pt-6">
                    <div className="p-4 bg-slate-900/40 rounded-xl leading-relaxed text-slate-350 text-sm">
                      <p dangerouslySetInnerHTML={{ __html: `<strong>Analysis Summary:</strong> ${analysisResult.explanation}` }} />
                    </div>
                    <a
                      href={`${BASE_URL}${analysisResult.report_url}`}
                      download
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-lg text-sm font-semibold transition-all shadow-lg shadow-indigo-650/15"
                    >
                      <Download className="w-4 h-4" />
                      Download Forensic Analysis Report (PDF)
                    </a>
                  </div>
                </div>
              )}

              {/* FACE DETECTION TAB */}
              {activeTab === 'face' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
                  <div className="border border-slate-800 rounded-xl overflow-hidden shadow-lg bg-slate-950/40">
                    <img 
                      src={`${BASE_URL}${analysisResult.visuals.face_url}`} 
                      alt="Face Detection Box" 
                      className="w-full object-contain max-h-[350px]" 
                    />
                  </div>
                  <div className="space-y-5">
                    <h3 className="text-white font-extrabold text-xl">MediaPipe Face Detection</h3>
                    <div className="space-y-3">
                      <div>
                        <p className="text-xs uppercase tracking-wider font-bold text-slate-500">Bounding Box Coordinates</p>
                        <p className="font-mono text-sm text-slate-200 mt-1">{analysisResult.face_coords}</p>
                      </div>
                      <div>
                        <p className="text-xs uppercase tracking-wider font-bold text-slate-500">Detector Confidence Score</p>
                        <p className="text-sm text-slate-200 mt-1">{(analysisResult.face_confidence * 100).toFixed(2)}%</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* EYE DETECTION TAB */}
              {activeTab === 'eyes' && (
                <div className="space-y-6">
                  <h3 className="text-white font-extrabold text-xl">MediaPipe Face Mesh Localization</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Annotated Mesh Visual */}
                    <div className="border border-slate-800 rounded-xl overflow-hidden bg-slate-950/40 p-2">
                      <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 px-1">Iris Centers Alignment</p>
                      <img 
                        src={`${BASE_URL}${analysisResult.visuals.mesh_url}`} 
                        alt="Iris Mesh Annotation" 
                        className="w-full object-contain max-h-[300px] rounded-lg"
                      />
                    </div>
                    {/* Left & Right Crops */}
                    <div className="space-y-4">
                      <div className="border border-slate-800 bg-slate-950/30 p-4 rounded-xl flex items-center gap-6">
                        <img 
                          src={`${BASE_URL}${analysisResult.visuals.l_crop_url}`} 
                          alt="Left Eye Crop" 
                          className="w-20 h-20 rounded-lg object-cover border border-emerald-500/30"
                        />
                        <div>
                          <h4 className="text-white font-bold text-sm">Left Eye Region Crop</h4>
                          <p className="text-slate-500 text-xs mt-1">MediaPipe Landmarks [468 - 472]</p>
                        </div>
                      </div>
                      <div className="border border-slate-800 bg-slate-950/30 p-4 rounded-xl flex items-center gap-6">
                        <img 
                          src={`${BASE_URL}${analysisResult.visuals.r_crop_url}`} 
                          alt="Right Eye Crop" 
                          className="w-20 h-20 rounded-lg object-cover border border-red-500/30"
                        />
                        <div>
                          <h4 className="text-white font-bold text-sm">Right Eye Region Crop</h4>
                          <p className="text-slate-500 text-xs mt-1">MediaPipe Landmarks [473 - 477]</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* REFLECTION TAB */}
              {activeTab === 'reflection' && (
                <div className="space-y-6">
                  <h3 className="text-white font-extrabold text-xl">Specular Highlight Blobs Extraction</h3>
                  
                  {/* Binary masks */}
                  <div className="grid grid-cols-2 gap-6">
                    <div className="border border-slate-800 bg-slate-950/30 p-4 rounded-xl text-center">
                      <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Left Highlight Mask</p>
                      <img 
                        src={`${BASE_URL}${analysisResult.visuals.l_refl_url}`} 
                        alt="Left Specular Mask" 
                        className="mx-auto w-24 h-24 object-contain rounded border border-slate-800 bg-black"
                      />
                    </div>
                    <div className="border border-slate-800 bg-slate-950/30 p-4 rounded-xl text-center">
                      <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Right Highlight Mask</p>
                      <img 
                        src={`${BASE_URL}${analysisResult.visuals.r_refl_url}`} 
                        alt="Right Specular Mask" 
                        className="mx-auto w-24 h-24 object-contain rounded border border-slate-800 bg-black"
                      />
                    </div>
                  </div>

                  {/* Metrics Table */}
                  <div className="border border-slate-800 rounded-xl overflow-hidden bg-slate-950/20 mt-6">
                    <table className="w-full text-left text-sm border-collapse">
                      <thead>
                        <tr className="bg-slate-950/40 text-slate-400 font-bold border-b border-slate-850">
                          <th className="py-3 px-4">Metric Dimension</th>
                          <th className="py-3 px-4">Left Eye Highlight</th>
                          <th className="py-3 px-4">Right Eye Highlight</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-850 text-slate-300">
                        <tr>
                          <td className="py-3 px-4 font-semibold">Centroid Coordinates (X, Y)</td>
                          <td className="py-3 px-4 font-mono text-xs">({analysisResult.blobs_details.left.position[0]}, {analysisResult.blobs_details.left.position[1]})</td>
                          <td className="py-3 px-4 font-mono text-xs">({analysisResult.blobs_details.right.position[0]}, {analysisResult.blobs_details.right.position[1]})</td>
                        </tr>
                        <tr>
                          <td className="py-3 px-4 font-semibold">Blob Area Size</td>
                          <td className="py-3 px-4">{analysisResult.blobs_details.left.area.toFixed(1)} pixels</td>
                          <td className="py-3 px-4">{analysisResult.blobs_details.right.area.toFixed(1)} pixels</td>
                        </tr>
                        <tr>
                          <td className="py-3 px-4 font-semibold">Blob Brightness Intensity</td>
                          <td className="py-3 px-4">{analysisResult.blobs_details.left.brightness.toFixed(2)}</td>
                          <td className="py-3 px-4">{analysisResult.blobs_details.right.brightness.toFixed(2)}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* METRICS INDEX TAB */}
              {activeTab === 'metrics' && (
                <div className="space-y-6">
                  <h3 className="text-white font-extrabold text-xl">Ocular Forensic Indices</h3>

                  <div className="space-y-6">
                    {/* RSI */}
                    <div className="bg-slate-950/20 border border-slate-800 p-5 rounded-xl space-y-2">
                      <div className="flex justify-between items-center text-sm font-semibold">
                        <span className="text-white">Reflection Symmetry Index (RSI)</span>
                        <span className="text-indigo-400">{analysisResult.rsi.toFixed(4)}</span>
                      </div>
                      <div className="w-full bg-slate-900 h-2.5 rounded-full overflow-hidden">
                        <div className="bg-indigo-500 h-full" style={{ width: `${analysisResult.rsi * 100}%` }}></div>
                      </div>
                      <p className="text-xs text-slate-500">Interpretation range: Highly Symmetric (0.90 - 1.00) | Suspicious (Below 0.70)</p>
                    </div>

                    {/* CRCS */}
                    <div className="bg-slate-950/20 border border-slate-800 p-5 rounded-xl space-y-2">
                      <div className="flex justify-between items-center text-sm font-semibold">
                        <span className="text-white">Corneal Reflection Consistency Score (CRCS)</span>
                        <span className="text-indigo-400">{analysisResult.crcs.toFixed(2)} / 100</span>
                      </div>
                      <div className="w-full bg-slate-900 h-2.5 rounded-full overflow-hidden">
                        <div className="bg-indigo-500 h-full" style={{ width: `${analysisResult.crcs}%` }}></div>
                      </div>
                      <p className="text-xs text-slate-500">Interpretation range: Real (80 - 100) | Suspicious (50 - 79) | Deepfake (Below 49)</p>
                    </div>

                    {/* SSIM */}
                    <div className="bg-slate-950/20 border border-slate-800 p-5 rounded-xl space-y-2">
                      <div className="flex justify-between items-center text-sm font-semibold">
                        <span className="text-white">Reflection Structural Similarity (SSIM)</span>
                        <span className="text-indigo-400">{analysisResult.ssim.toFixed(4)}</span>
                      </div>
                      <div className="w-full bg-slate-900 h-2.5 rounded-full overflow-hidden">
                        <div className="bg-indigo-500 h-full" style={{ width: `${analysisResult.ssim * 100}%` }}></div>
                      </div>
                      <p className="text-xs text-slate-500">Compares structure of cropped specular region (0.00 to 1.00)</p>
                    </div>
                  </div>
                </div>
              )}

              {/* VISUAL ANALYSIS TAB */}
              {activeTab === 'visual' && (
                <div className="space-y-6">
                  <h3 className="text-white font-extrabold text-xl">Symmetry Overlap Verification</h3>
                  <div className="border border-slate-800 rounded-xl overflow-hidden bg-slate-950/40 p-4 max-w-md mx-auto text-center">
                    <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Left (Green Contour) vs Right (Red Contour) Highlights</p>
                    <img 
                      src={`${BASE_URL}${analysisResult.visuals.comparison_url}`} 
                      alt="Specular Overlap Comparison" 
                      className="mx-auto max-h-[300px] object-contain border border-slate-800 rounded bg-slate-900 shadow-inner"
                    />
                  </div>
                  <p className="text-xs text-slate-500 text-center leading-relaxed max-w-lg mx-auto">
                    Specular reflection shapes segmenting from both eyes are compared here. Geometric coordinates discrepancies correspond to GAN synthesis artifacts.
                  </p>
                </div>
              )}

            </div>
          </div>
        )}

      </main>
    </div>
  );
}

export default Workspace;
