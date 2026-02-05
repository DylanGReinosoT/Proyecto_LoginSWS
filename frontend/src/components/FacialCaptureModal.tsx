import React, { useRef, useEffect, useState } from 'react';
import { AlertCircle, Loader, CheckCircle } from 'lucide-react';
import { FaceLandmarker, FilesetResolver } from '@mediapipe/tasks-vision';

interface FacialCaptureModalProps {
  isOpen: boolean;
  onCapture: (imageBase64: string) => void;
  onClose: () => void;
  isLoading?: boolean;
  mode: 'capture' | 'verify';
  title?: string;
  description?: string;
  authToken?: string;
}

const FacialCaptureModal: React.FC<FacialCaptureModalProps> = ({
  isOpen,
  onCapture,
  onClose,
  isLoading = false,
  mode = 'capture',
  title = '📸 Registro Facial - Paso Obligatorio',
  description = 'Por favor, mire directamente a la cámara y parpadee 3 veces para completar su registro de forma segura',
  authToken = '',
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const overlayCanvasRef = useRef<HTMLCanvasElement>(null);
  const [cameraPermission, setCameraPermission] = useState<'pending' | 'granted' | 'denied'>('pending');
  const [blinkCount, setBlinkCount] = useState(0);
  const [isCaptured, setIsCaptured] = useState(false);
  const [error, setError] = useState('');
  const [capturedImage, setCapturedImage] = useState<string>('');
  const [instructions, setInstructions] = useState('Solicitando acceso a la cámara...');
  const [eyesClosed, setEyesClosed] = useState(false);
  const [faceDetected, setFaceDetected] = useState(false);
  const [eyeOpenRatio, setEyeOpenRatio] = useState(0);
  const [diagnosticMessage, setDiagnosticMessage] = useState('');
  
  // References
  const prevEyesClosedRef = useRef(false);
  const faceLandmarkerRef = useRef<FaceLandmarker | null>(null);
  const stableBlinkCountRef = useRef(0);
  const eyeOpenRatioRef = useRef(0);
  const frameCountRef = useRef(0);

  // Solicitar acceso a la cámara
  useEffect(() => {
    if (!isOpen) return;

    const startCamera = async () => {
      try {
        setError('');
        setBlinkCount(0);
        setIsCaptured(false);
        setCapturedImage('');
        stableBlinkCountRef.current = 0;
        prevEyesClosedRef.current = false;
        eyeOpenRatioRef.current = 0;
        frameCountRef.current = 0;
        
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: 'user',
            width: { ideal: 1280 },
            height: { ideal: 960 },
          },
        });

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          setCameraPermission('granted');
          setInstructions('✓ Cámara lista. Acércate a la cámara y parpadea 3 veces lentamente.');
        }
      } catch (err) {
        setCameraPermission('denied');
        setError('No se pudo acceder a la cámara. Por favor, verifica los permisos.');
        setInstructions('❌ Error: No se pudo acceder a la cámara');
      }
    };

    startCamera();

    return () => {
      if (videoRef.current?.srcObject) {
        const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
        tracks.forEach(track => track.stop());
      }
    };
  }, [isOpen]);

  // Detección de rostros y puntos faciales con MediaPipe FaceLandmarker
  useEffect(() => {
    if (!isOpen || cameraPermission !== 'granted' || isCaptured) return;

    let animationFrameId: number;

    const initializeMediaPipe = async () => {
      try {
        console.log('[MediaPipe] Iniciando FaceLandmarker...');
        const vision = await FilesetResolver.forVisionTasks(
          'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm'
        );
        
        console.log('[MediaPipe] FilesetResolver cargado');
        
        faceLandmarkerRef.current = await FaceLandmarker.createFromOptions(vision, {
          baseOptions: {
            modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task'
          },
          runningMode: 'VIDEO',
          numFaces: 1,
        });
        
        console.log('[MediaPipe] FaceLandmarker initialized exitosamente');
      } catch (error) {
        console.error('[MediaPipe] Error inicializando:', error);
        setError('Error inicializando detección facial. Por favor recarga la página.');
      }
    };

    const detectFaceAndBlinks = async () => {
      if (!videoRef.current || !faceLandmarkerRef.current) {
        return;
      }

      const video = videoRef.current;
      
      if (video.videoWidth === 0 || video.videoHeight === 0) {
        animationFrameId = requestAnimationFrame(detectFaceAndBlinks);
        return;
      }

      try {
        const results = faceLandmarkerRef.current.detectForVideo(video, performance.now());

        if (results.faceLandmarks && results.faceLandmarks.length > 0) {
          const landmarks = results.faceLandmarks[0];
          console.log('[Face] Rostro detectado con landmarks');
          
          setFaceDetected(true);

          if (blinkCount === 0) {
            setInstructions('✓ Rostro detectado | Parpadea lentamente 3 veces para continuar');
          }

          // DETECCIÓN DE PARPADEOS usando landmarks de ojos
          // Eye landmarks indices:
          // Left eye: top=159, bottom=145, left=133, right=33
          // Right eye: top=386, bottom=374, left=362, right=263
          
          const leftEyeTop = landmarks[159];
          const leftEyeBottom = landmarks[145];
          const rightEyeTop = landmarks[386];
          const rightEyeBottom = landmarks[374];

          // Calcular distancia vertical de cada ojo (apertura ocular)
          const leftEyeOpenness = Math.abs(leftEyeTop.y - leftEyeBottom.y);
          const rightEyeOpenness = Math.abs(rightEyeTop.y - rightEyeBottom.y);
          
          // Promedio de apertura ocular normalizado (0-100)
          const eyeOpenness = (leftEyeOpenness + rightEyeOpenness) / 2 * 1000;
          const normalizedRatio = Math.max(0, Math.min(100, eyeOpenness));
          
          eyeOpenRatioRef.current = normalizedRatio;
          setEyeOpenRatio(Math.round(normalizedRatio));

          // Umbral de detección: > 20% = ojos abiertos, < 20% = ojos cerrados
          const eyesAreOpen = normalizedRatio > 20;
          const eyesWereClosed = prevEyesClosedRef.current;

          frameCountRef.current++;
          if (frameCountRef.current % 5 === 0) {
            console.log(`[Eyes] Frame ${frameCountRef.current}: Ratio=${normalizedRatio.toFixed(1)}%, Open=${eyesAreOpen}, WasClosed=${eyesWereClosed}`);
          }

          // DETECCIÓN DE PARPADEO: transición de cerrados a abiertos
          if (eyesAreOpen && eyesWereClosed) {
            console.log(`[✓ PARPADEO CONFIRMADO!] Ratio cambió de closed (${(eyeOpenRatioRef.current - 5).toFixed(1)}%) a open (${normalizedRatio.toFixed(1)}%)`);
            
            stableBlinkCountRef.current += 1;
            const newCount = stableBlinkCountRef.current;
            
            setBlinkCount(newCount);
            console.log(`[✓ Blink #${newCount}/3 Detectado]`);
            
            prevEyesClosedRef.current = false;
            
            if (newCount >= 3) {
              setInstructions('✅ ¡3 parpadeos detectados! Capturando imagen...');
              setTimeout(() => captureImage(), 500);
            } else {
              setInstructions(`✓ Parpadeo #${newCount} detectado | Faltan ${3 - newCount} parpadeo(s) más`);
            }
          }

          // Actualizar estado de ojos
          prevEyesClosedRef.current = !eyesAreOpen;
          setEyesClosed(!eyesAreOpen);

          // Mensaje diagnóstico
          if (!eyesAreOpen) {
            setDiagnosticMessage('👁️ Ojos detectados como CERRADOS - Parpadea');
          } else {
            setDiagnosticMessage('✓ Ojos detectados como ABIERTOS - Parpadea');
          }

          // DIBUJAR LANDMARKS EN CANVAS
          if (overlayCanvasRef.current) {
            overlayCanvasRef.current.width = video.videoWidth;
            overlayCanvasRef.current.height = video.videoHeight;
            const ctx = overlayCanvasRef.current.getContext('2d');
            if (ctx) {
              ctx.clearRect(0, 0, overlayCanvasRef.current.width, overlayCanvasRef.current.height);

              // Dibujar todos los landmarks
              landmarks.forEach((landmark, index) => {
                const x = landmark.x * video.videoWidth;
                const y = landmark.y * video.videoHeight;

                // Colorear puntos específicos
                let color = '#22c55e'; // Verde por defecto
                let radius = 3;

                // Destacar puntos de ojos
                if (index === 159 || index === 145) {
                  color = eyesAreOpen ? '#ff6b6b' : '#ffa500'; // Rojo para ojos abiertos, naranja para cerrados
                  radius = 5;
                } else if (index === 386 || index === 374) {
                  color = eyesAreOpen ? '#ff6b6b' : '#ffa500';
                  radius = 5;
                }
                // Puntos de rostro principal
                else if (
                  index === 10 || index === 152 || index === 21 || index === 251 || // Contorno principal
                  index === 200 || index === 199 || index === 175 || index === 171 || // Mejillas
                  index === 50 || index === 280 // Frente
                ) {
                  color = '#00bcd4';
                  radius = 4;
                }

                // Dibujar punto
                ctx.fillStyle = color;
                ctx.beginPath();
                ctx.arc(x, y, radius, 0, 2 * Math.PI);
                ctx.fill();
              });

              // Dibujar conexiones entre puntos clave (contorno de cara)
              const contourIndices = [
                10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109, 10
              ];

              ctx.strokeStyle = '#00bcd4';
              ctx.lineWidth = 2;
              ctx.beginPath();
              contourIndices.forEach((idx, i) => {
                if (idx < landmarks.length) {
                  const x = landmarks[idx].x * video.videoWidth;
                  const y = landmarks[idx].y * video.videoHeight;
                  if (i === 0) {
                    ctx.moveTo(x, y);
                  } else {
                    ctx.lineTo(x, y);
                  }
                }
              });
              ctx.stroke();

              // Dibujar conexiones de ojos
              const leftEyeIndices = [133, 173, 157, 158, 159, 160, 161, 246, 33];
              const rightEyeIndices = [362, 398, 384, 385, 386, 387, 388, 466, 263];

              ctx.strokeStyle = eyesAreOpen ? '#ff6b6b' : '#ffa500';
              ctx.lineWidth = 2;

              // Dibujar ojo izquierdo
              ctx.beginPath();
              leftEyeIndices.forEach((idx, i) => {
                if (idx < landmarks.length) {
                  const x = landmarks[idx].x * video.videoWidth;
                  const y = landmarks[idx].y * video.videoHeight;
                  if (i === 0) {
                    ctx.moveTo(x, y);
                  } else {
                    ctx.lineTo(x, y);
                  }
                }
              });
              ctx.closePath();
              ctx.stroke();

              // Dibujar ojo derecho
              ctx.beginPath();
              rightEyeIndices.forEach((idx, i) => {
                if (idx < landmarks.length) {
                  const x = landmarks[idx].x * video.videoWidth;
                  const y = landmarks[idx].y * video.videoHeight;
                  if (i === 0) {
                    ctx.moveTo(x, y);
                  } else {
                    ctx.lineTo(x, y);
                  }
                }
              });
              ctx.closePath();
              ctx.stroke();
            }
          }
        } else {
          // No face detected
          console.log('[Face] Sin detecciones');
          setFaceDetected(false);
          setEyesClosed(false);
          setEyeOpenRatio(0);
          setDiagnosticMessage('');
          prevEyesClosedRef.current = false;
          eyeOpenRatioRef.current = 0;

          if (overlayCanvasRef.current) {
            const ctx = overlayCanvasRef.current.getContext('2d');
            if (ctx) {
              ctx.clearRect(0, 0, overlayCanvasRef.current.width, overlayCanvasRef.current.height);
            }
          }
          
          if (blinkCount === 0) {
            setInstructions('⚠️ No hay rostro detectado. No se puede capturar.');
          }
        }
      } catch (error) {
        console.error('[Detect] Error in face detection:', error);
      }

      animationFrameId = requestAnimationFrame(detectFaceAndBlinks);
    };

    initializeMediaPipe().then(() => {
      if (faceLandmarkerRef.current) {
        animationFrameId = requestAnimationFrame(detectFaceAndBlinks);
      }
    });

    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
    };
  }, [isOpen, cameraPermission, isCaptured]);

  const captureImage = () => {
    if (videoRef.current && canvasRef.current) {
      const context = canvasRef.current.getContext('2d');
      if (context) {
        canvasRef.current.width = videoRef.current.videoWidth;
        canvasRef.current.height = videoRef.current.videoHeight;
        context.drawImage(videoRef.current, 0, 0);
        
        const imageBase64 = canvasRef.current.toDataURL('image/jpeg').split(',')[1];
        setCapturedImage(canvasRef.current.toDataURL('image/jpeg'));
        setIsCaptured(true);
        setInstructions('✅ Imagen capturada correctamente');
        
        onCapture(imageBase64);
      }
    }
  };

  const handleRetake = () => {
    setBlinkCount(0);
    setIsCaptured(false);
    setCapturedImage('');
    setEyesClosed(false);
    setEyeOpenRatio(0);
    setDiagnosticMessage('');
    prevEyesClosedRef.current = false;
    eyeOpenRatioRef.current = 0;
    frameCountRef.current = 0;
    stableBlinkCountRef.current = 0;
    setFaceDetected(false);
    setInstructions('✓ Cámara lista. Acércate a la cámara y parpadea 3 veces lentamente.');
  };

  const handleClose = () => {
    if (videoRef.current?.srcObject) {
      const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
      tracks.forEach(track => track.stop());
    }
    onClose();
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-background rounded-3xl w-full max-w-3xl p-8 border border-border max-h-[90vh] overflow-y-auto">
        {/* Encabezado */}
        <div className="mb-8 text-center">
          <h2 className="text-3xl font-bold mb-3">{title}</h2>
          <p className="text-muted-foreground text-base">{description}</p>
        </div>

        {/* Video con detección de landmarks */}
        <div className="relative mb-8 rounded-2xl overflow-hidden bg-black aspect-video flex items-center justify-center border-2 border-coral/30">
          {!isCaptured ? (
            <>
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover"
              />
              {/* Overlay con landmarks faciales */}
              <canvas
                ref={overlayCanvasRef}
                className="absolute inset-0 w-full h-full"
              />
            </>
          ) : (
            <img src={capturedImage} alt="Captura facial" className="w-full h-full object-cover" />
          )}
          
          {cameraPermission === 'pending' && (
            <div className="absolute inset-0 bg-black/75 flex items-center justify-center">
              <div className="text-center">
                <Loader className="w-16 h-16 text-coral animate-spin mx-auto mb-4" />
                <p className="text-white text-base">Solicitando acceso a cámara...</p>
              </div>
            </div>
          )}

          {/* Canvas oculto para captura */}
          <canvas ref={canvasRef} className="hidden" />

          {/* Indicador de parpadeos */}
          {!isCaptured && cameraPermission === 'granted' && (
            <div className="absolute top-6 right-6 bg-black/80 text-white px-6 py-3 rounded-xl text-lg font-bold border border-coral/50 backdrop-blur">
              Parpadeos: <span className="text-coral">{blinkCount}/3</span>
            </div>
          )}

          {/* Indicador de apertura ocular */}
          {!isCaptured && cameraPermission === 'granted' && faceDetected && (
            <div className="absolute bottom-6 right-6 bg-black/80 text-white px-4 py-2 rounded-lg text-sm border border-blue-500/50 backdrop-blur">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold">Ojos: {eyeOpenRatio}%</span>
                <div className="w-32 h-4 bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    className={`h-full transition-all ${eyeOpenRatio > 20 ? 'bg-red-500' : 'bg-orange-500'}`}
                    style={{ width: `${Math.min(eyeOpenRatio, 100)}%` }}
                  ></div>
                </div>
              </div>
            </div>
          )}

          {/* Mensaje de diagnóstico */}
          {!isCaptured && cameraPermission === 'granted' && faceDetected && diagnosticMessage && (
            <div className="absolute bottom-6 left-6 bg-black/80 text-white px-4 py-3 rounded-lg text-sm border border-yellow-500/50 backdrop-blur max-w-xs">
              {diagnosticMessage}
            </div>
          )}

          {/* Indicador de rostro detectado */}
          {!isCaptured && cameraPermission === 'granted' && (
            <div className="absolute top-6 left-6 bg-black/80 text-white px-6 py-3 rounded-xl text-sm border backdrop-blur"
              style={{borderColor: faceDetected ? '#22c55e' : '#f97316'}}>
              {faceDetected ? (
                <span className="flex items-center gap-2 text-green-500">
                  <span className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
                  ✓ Rostro detectado
                </span>
              ) : (
                <span className="flex items-center gap-2 text-orange-500">
                  <span className="w-3 h-3 bg-orange-500 rounded-full animate-pulse"></span>
                  No hay rostro detectado. No se puede capturar.
                </span>
              )}
            </div>
          )}

          {/* Indicador de éxito */}
          {isCaptured && (
            <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
              <CheckCircle className="w-24 h-24 text-green-500 animate-bounce" />
            </div>
          )}
        </div>

        {/* Mensaje de estado */}
        <div className="mb-8 p-4 bg-secondary/50 rounded-xl text-center border border-border">
          <p className="text-base text-foreground font-medium">{instructions}</p>
          
          {/* Instrucciones detalladas */}
          {faceDetected && blinkCount === 0 && !isCaptured && (
            <div className="mt-4 pt-4 border-t border-border text-sm text-muted-foreground">
              <p className="mb-2"><strong>💡 Consejos para detectar parpadeos:</strong></p>
              <ul className="text-left space-y-1 text-xs">
                <li>✓ Asegúrate de que haya buena iluminación en tu cara</li>
                <li>✓ Mira fijo a la cámara y parpadea lentamente y naturalmente</li>
                <li>✓ La máscara de puntos debe verse estable alrededor de tu rostro</li>
                <li>✓ Los puntos de los ojos deben cambiar de color cuando parpadees</li>
              </ul>
            </div>
          )}

          {/* Progreso de parpadeos detectados */}
          {faceDetected && blinkCount > 0 && !isCaptured && (
            <div className="mt-4 pt-4 border-t border-border">
              <div className="flex gap-2 justify-center">
                {[1, 2, 3].map(i => (
                  <div 
                    key={i} 
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm ${
                      i <= blinkCount 
                        ? 'bg-green-500/20 border-2 border-green-500 text-green-500' 
                        : 'bg-gray-700/20 border-2 border-gray-600 text-gray-400'
                    }`}
                  >
                    {i <= blinkCount ? '✓' : i}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="mb-8 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start gap-3">
            <AlertCircle className="w-6 h-6 text-red-500 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-500">{error}</p>
          </div>
        )}

        {/* Botones */}
        <div className="flex gap-4">
          {!isCaptured ? (
            <>
              <button
                onClick={handleClose}
                disabled={isLoading}
                className="flex-1 px-6 py-3 border border-border rounded-xl text-foreground hover:bg-secondary transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancelar
              </button>
              {cameraPermission === 'denied' && (
                <button
                  onClick={handleClose}
                  className="flex-1 px-6 py-3 bg-red-600 text-white rounded-xl font-semibold hover:bg-red-700 transition-colors"
                >
                  ❌ Sin acceso a cámara
                </button>
              )}
            </>
          ) : (
            <>
              <button
                onClick={handleRetake}
                disabled={isLoading}
                className="flex-1 px-6 py-3 border border-border rounded-xl text-foreground hover:bg-secondary transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                🔄 Reintentar
              </button>
              <button
                onClick={handleClose}
                disabled={isLoading}
                className="flex-1 px-6 py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
              >
                {isLoading ? (
                  <>
                    <Loader className="w-5 h-5 animate-spin" />
                    Procesando...
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-5 h-5" />
                    Continuar ✓
                  </>
                )}
              </button>
            </>
          )}
        </div>

        {/* Nota de privacidad */}
        <p className="mt-6 text-xs text-muted-foreground text-center">
          {mode === 'capture'
            ? 'Tu imagen facial se guardará de forma segura para futuras verificaciones.'
            : 'Tu imagen será verificada y no se almacenará.'}
        </p>
      </div>
    </div>
  );
};

export default FacialCaptureModal;
