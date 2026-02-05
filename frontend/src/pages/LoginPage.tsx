import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Eye, EyeOff, Mail, Lock, ArrowRight, Sparkles } from "lucide-react";
import cosmicLandscape from "@/assets/cosmic-landscape.jpg";
import FacialCaptureModal from "@/components/FacialCaptureModal";

interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  message: string;
  next_step: string;
  facial_recognition_enabled: boolean;
}

const LoginPage = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isExiting, setIsExiting] = useState(false);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [error, setError] = useState("");
  const [showFacialModal, setShowFacialModal] = useState(false);
  const [loginData, setLoginData] = useState<LoginResponse | null>(null);
  const [isVerifyingFacial, setIsVerifyingFacial] = useState(false);

  const slides = [
    {
      title: "Descubre mundos infinitos",
      description: "Donde la creatividad no tiene límites y cada idea cobra vida.",
    },
    {
      title: "Integrantes Del Equipo",
      description: "Pamela Chipe, Kleber Chavez, Gabriel Reiniso.",
    },
    {
      title: "Proyectos Innovadores",
      description: "Desarrollo de aplicaciones creativas y soluciones tecnológicas.",
    },
  ];

  const handlePrevSlide = () => {
    setCurrentSlide((prev) => (prev === 0 ? slides.length - 1 : prev - 1));
  };

  const handleNextSlide = () => {
    setCurrentSlide((prev) => (prev === slides.length - 1 ? 0 : prev + 1));
  };

  const handleDotClick = (index: number) => {
    setCurrentSlide(index);
  };

  // Auto-advance slides cada 5 segundos
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev === slides.length - 1 ? 0 : prev + 1));
    }, 5000);

    return () => clearInterval(interval);
  }, [slides.length]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email,
          password: password,
        }),
      });

      const data: LoginResponse = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Credenciales inválidas. Por favor, verifica email y contraseña.");
      }

      // ✅ Credenciales válidas
      // Ahora se REQUIERE verificación facial para completar el login
      setLoginData(data);
      setShowFacialModal(true);
      setIsLoading(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Error desconocido";
      setError(errorMessage);
      console.error("❌ Error en login:", errorMessage);
      setIsLoading(false);
    }
  };

  const handleFacialVerification = async (imageBase64: string) => {
    if (!loginData) return;

    setIsVerifyingFacial(true);
    setError("");

    try {
      // ✅ VERIFICACIÓN CRÍTICA: Enviar a nueva ruta que valida que el rostro pertenezca al usuario
      const response = await fetch(
        `http://localhost:8000/api/auth/verify-facial-for-login?user_id=${loginData.user_id}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            image_base64: imageBase64,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        // Manejo detallado de errores
        if (response.status === 401) {
          // Cualquier error 401 significa que el rostro NO pertenece al usuario
          throw new Error("❌ " + (data.detail || "El rostro no pertenece a este usuario. Acceso denegado."));
        } else if (response.status === 400) {
          throw new Error("❌ " + (data.detail || "Error en la detección del rostro. Por favor, asegúrate de estar mirando la cámara."));
        } else if (response.status === 403) {
          throw new Error("❌ " + (data.detail || "Facial recognition no habilitado para tu cuenta."));
        } else {
          throw new Error("❌ " + (data.detail || "Error en la verificación facial"));
        }
      }

      // ✅ Verificación exitosa - Guardar token y navegar
      localStorage.setItem("access_token", loginData.access_token);
      localStorage.setItem("token_type", loginData.token_type);
      localStorage.setItem("user_id", loginData.user_id);

      setShowFacialModal(false);
      setIsExiting(true);

      // Transición animada al home
      setTimeout(() => {
        navigate("/home");
      }, 400);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "❌ Error en la verificación facial";
      setError(errorMessage);
      console.error("Error en verificación facial:", errorMessage);
      // Modal sigue abierto para que el usuario pueda reintentar
    } finally {
      setIsVerifyingFacial(false);
    }
  };

  return (
    <div className={`min-h-screen flex transition-all duration-500 ${isExiting ? "animate-page-out" : ""}`}>
      {/* Panel izquierdo - Imagen artística */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-dark-bg">
        {/* Imagen de fondo */}
        <div className="absolute inset-0 opacity-0 animate-fade-in animation-fill-both">
          <img
            src={cosmicLandscape}
            alt="Cosmic landscape"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-dark-bg/50 to-transparent" />
        </div>

        {/* Partículas flotantes */}
        {[...Array(12)].map((_, i) => (
          <div
            key={i}
            className="particle animate-twinkle"
            style={{
              width: `${Math.random() * 4 + 2}px`,
              height: `${Math.random() * 4 + 2}px`,
              top: `${Math.random() * 100}%`,
              left: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 3}s`,
              animationDuration: `${Math.random() * 2 + 2}s`,
            }}
          />
        ))}

        {/* Card con contenido */}
        <div className="absolute inset-8 flex flex-col justify-end opacity-0 animate-scale-in animation-delay-300 animation-fill-both">
          
          {/* Badge Superior (Opcional, si quieres que flote arriba) */}
          <div className="absolute top-0 left-0 glass rounded-full px-4 py-2 flex items-center gap-2 animate-float-slow">
            <Sparkles className="w-4 h-4 text-coral" />
            <span className="text-white text-xs font-bold uppercase tracking-wider">Portal Creativo</span>
          </div>

          {/* Contenedor Principal */}
          <div className="glass rounded-3xl p-8 backdrop-blur-md bg-black/20 border border-white/10 opacity-0 animate-fade-in animation-delay-500 animation-fill-both">
            
            <div className="transition-all duration-500 ease-in-out">
              <h2 className="font-display text-4xl md:text-5xl text-white font-bold leading-tight mb-3">
                {slides[currentSlide].title}
              </h2>
              <p className="text-white/80 text-lg leading-relaxed max-w-md">
                {slides[currentSlide].description}
              </p>
            </div>
            
            {/* Navegación Refinada */}
            <div className="flex items-center gap-4 mt-8">
              <div className="flex gap-2">
                {slides.map((_, i) => (
                  <button
                    key={i}
                    onClick={() => handleDotClick(i)}
                    className={`h-2 rounded-full transition-all duration-500 cursor-pointer ${
                      i === currentSlide 
                        ? "w-10 bg-coral shadow-[0_0_10px_rgba(255,127,80,0.5)]" 
                        : "w-2 bg-white/30 hover:bg-white/50"
                    }`}
                    aria-label={`Go to slide ${i + 1}`}
                  />
                ))}
              </div>
            </div>

          </div>
        </div>

        {/* Círculos decorativos animados */}
        <div className="absolute -bottom-20 -left-20 w-64 h-64 rounded-full border border-white/10 animate-rotate-slow" />
        <div className="absolute -top-10 -right-10 w-40 h-40 rounded-full border border-coral/20 animate-rotate-slow" style={{ animationDirection: 'reverse' }} />
      </div>

      {/* Panel derecho - Formulario */}
      <div className="flex-1 flex items-center justify-center p-8 bg-background">
        <div className="w-full max-w-md">
          {/* Logo */}
          <div className="text-center mb-12 opacity-0 animate-fade-in animation-fill-both">
            <h1 className="font-display text-3xl font-bold tracking-tight">
              Proyecto Desarrollo de <span className="text-coral"> Software Seguro</span>
            </h1>
          </div>

          {/* Título de bienvenida */}
          <div className="text-center mb-10 opacity-0 animate-fade-in animation-delay-200 animation-fill-both">
            <h2 className="font-display text-4xl md:text-5xl font-bold mb-3">
              Hola <span className="text-coral">Estudiante</span>
            </h2>
            <p className="text-muted-foreground text-lg">
              Bienvenido de vuelta 
            </p>
          </div>

          {/* Mensaje de error - Mejorado */}
          {error && (
            <div className="mb-6 opacity-0 animate-slide-up animation-fill-both p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-start gap-3">
              <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <div>
                <p className="text-red-500 text-sm font-semibold">❌ Error</p>
                <p className="text-red-500 text-sm mt-1">{error}</p>
              </div>
            </div>
          )}

          {/* Formulario */}
          <form onSubmit={handleLogin} className="space-y-6">
            {/* Campo Email */}
            <div className="opacity-0 animate-slide-up animation-delay-300 animation-fill-both">
              <div className="relative group input-glow rounded-xl transition-all duration-300">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground group-focus-within:text-coral transition-colors duration-300" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Email"
                  className="w-full pl-12 pr-4 py-4 bg-secondary border border-border rounded-xl focus:outline-none focus:border-coral transition-all duration-300 text-foreground placeholder:text-muted-foreground"
                  required
                />
              </div>
            </div>

            {/* Campo Password */}
            <div className="opacity-0 animate-slide-up animation-delay-400 animation-fill-both">
              <div className="relative group input-glow rounded-xl transition-all duration-300">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground group-focus-within:text-coral transition-colors duration-300" />
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Contraseña"
                  className="w-full pl-12 pr-12 py-4 bg-secondary border border-border rounded-xl focus:outline-none focus:border-coral transition-all duration-300 text-foreground placeholder:text-muted-foreground"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-coral transition-colors duration-300"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              <div className="flex justify-end mt-2">
                <button type="button" className="text-sm text-coral hover:underline transition-all">
                  ¿Olvidaste tu contraseña?
                </button>
              </div>
            </div>

            {/* Separador */}
            <div className="flex items-center gap-4 opacity-0 animate-slide-up animation-delay-500 animation-fill-both">
              <div className="flex-1 h-px bg-border" />
              <span className="text-muted-foreground text-sm">o</span>
              <div className="flex-1 h-px bg-border" />
            </div>

            {/* Login con Google */}
            <button
              type="button"
              className="w-full py-4 bg-secondary border border-border rounded-xl flex items-center justify-center gap-3 hover:bg-muted transition-all duration-300 hover:scale-[1.02] opacity-0 animate-slide-up animation-delay-500 animation-fill-both"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path
                  fill="currentColor"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              <span className="font-medium">Continuar con Google</span>
            </button>

            {/* Botón de Login */}
            <button
              type="submit"
              disabled={isLoading}
              className={`w-full py-4 bg-coral text-white rounded-xl font-semibold flex items-center justify-center gap-2 transition-all duration-300 hover:bg-coral-dark hover:scale-[1.02] opacity-0 animate-slide-up animation-delay-600 animation-fill-both ${
                isLoading ? "animate-pulse-glow" : "hover:shadow-lg hover:shadow-coral/30"
              }`}
            >
              {isLoading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Ingresando...</span>
                </>
              ) : (
                <>
                  <span>Ingresar</span>
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>

          {/* Link de registro */}
          <p className="text-center mt-8 text-muted-foreground opacity-0 animate-fade-in animation-delay-700 animation-fill-both">
            ¿No tienes cuenta?{" "}
            <Link to="/register" className="text-coral font-semibold hover:underline transition-all">
              Regístrate
            </Link>
          </p>

          {/* Iconos sociales */}
          <div className="flex items-center justify-center gap-6 mt-10 opacity-0 animate-fade-in animation-delay-800 animation-fill-both">
            {["facebook", "twitter", "linkedin", "instagram"].map((social, i) => (
              <button
                key={social}
                className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center text-muted-foreground hover:text-coral hover:bg-muted transition-all duration-300 hover:scale-110 hover:-translate-y-1"
                style={{ animationDelay: `${800 + i * 100}ms` }}
              >
                {social === "facebook" && (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
                  </svg>
                )}
                {social === "twitter" && (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z" />
                  </svg>
                )}
                {social === "linkedin" && (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                  </svg>
                )}
                {social === "instagram" && (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
                  </svg>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Modal de Verificación Facial - OBLIGATORIO para completar login */}
      <FacialCaptureModal
        isOpen={showFacialModal}
        onCapture={handleFacialVerification}
        onClose={() => setShowFacialModal(false)}
        isLoading={isVerifyingFacial}
        mode="verify"
        title="🔐 Verificación Facial - Paso Obligatorio"
        description="Por favor, mire directamente a la cámara y parpadee 3 veces para completar el login de forma segura"
        authToken={loginData?.access_token || ""}
      />
    </div>
  );
};

export default LoginPage;
