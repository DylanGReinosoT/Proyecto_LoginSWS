import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Eye, EyeOff, Mail, Lock, User, Sparkles, ArrowLeft, Check, X } from "lucide-react";
import cosmicLandscape from "@/assets/cosmic-landscape.jpg";
import FacialCaptureModal from "@/components/FacialCaptureModal";

interface PasswordRequirements {
  minLength: boolean;
  hasUppercase: boolean;
  hasLowercase: boolean;
  hasNumber: boolean;
  hasSpecialChar: boolean;
}

interface RegistrationResponse {
  user_id: string;
  email: string;
  username: string;
  full_name: string;
  is_active: boolean;
  message: string;
  next_step: string;
}

const RegisterPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    username: "",
    password: "",
    confirmPassword: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [currentSlide, setCurrentSlide] = useState(0);
  const [showFacialModal, setShowFacialModal] = useState(false);
  const [registrationData, setRegistrationData] = useState<RegistrationResponse | null>(null);
  const [isSavingFacial, setIsSavingFacial] = useState(false);
  const [facialImageBase64, setFacialImageBase64] = useState<string>("");
  const [passwordRequirements, setPasswordRequirements] = useState<PasswordRequirements>({
    minLength: false,
    hasUppercase: false,
    hasLowercase: false,
    hasNumber: false,
    hasSpecialChar: false,
  });

  const slides = [
    {
      title: "Únete a nuestra comunidad",
      description: "Seguridad avanzada con reconocimiento facial y autenticación moderna.",
    },
    {
      title: "Tu privacidad es importante",
      description: "Todos tus datos están protegidos con encriptación de grado empresarial.",
    },
    {
      title: "Comienza ahora",
      description: "Crea tu cuenta en segundos y accede a todas nuestras funciones.",
    },
  ];

  // Auto-advance slides
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev === slides.length - 1 ? 0 : prev + 1));
    }, 5000);

    return () => clearInterval(interval);
  }, [slides.length]);

  // Validar requisitos de contraseña
  useEffect(() => {
    const password = formData.password;
    setPasswordRequirements({
      minLength: password.length >= 8,
      hasUppercase: /[A-Z]/.test(password),
      hasLowercase: /[a-z]/.test(password),
      hasNumber: /\d/.test(password),
      hasSpecialChar: /[!@#$%^&*(),.?":{}|<>]/.test(password),
    });
  }, [formData.password]);

  const isPasswordValid = Object.values(passwordRequirements).every(Boolean);
  const isFormValid = 
    formData.full_name &&
    formData.email &&
    formData.username &&
    formData.password &&
    formData.confirmPassword === formData.password &&
    isPasswordValid;

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    
    // Primero pedir captura facial ANTES de registrar en BD
    setShowFacialModal(true);
  };

  const handleFacialCapture = async (imageBase64: string) => {
    setIsSavingFacial(true);
    setError("");

    try {
      // Registrar con la imagen facial capturada
      const registerResponse = await fetch("http://localhost:8000/api/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: formData.email,
          username: formData.username,
          password: formData.password,
          full_name: formData.full_name,
          facial_image_base64: imageBase64,  // Incluir imagen facial en registro
        }),
      });

      const data: RegistrationResponse = await registerResponse.json();

      if (!registerResponse.ok) {
        // Manejo específico de errores
        if (registerResponse.status === 409) {
          // Detectar si es error de rostro duplicado
          const errorDetail = data.detail || "";
          if (errorDetail.includes("rostro")) {
            throw new Error(
              "❌ Este rostro ya está registrado en el sistema. " +
              "Por favor, intenta con una foto diferente o crea una cuenta diferente."
            );
          } else {
            throw new Error("El email o nombre de usuario ya está registrado. Intenta con otro.");
          }
        } else if (registerResponse.status === 400) {
          throw new Error(data.message || "Datos inválidos. Verifica el formulario.");
        } else {
          throw new Error(data.detail || data.message || "Error al registrar usuario");
        }
      }

      // ✅ Registro exitoso con captura facial
      setRegistrationData(data);
      setShowFacialModal(false);
      
      // Mostrar mensaje de éxito y redirigir a login
      await new Promise((resolve) => setTimeout(resolve, 1500));
      navigate("/", { state: { message: "✅ Registro completado. Por favor, inicia sesión." } });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Error al registrar usuario";
      setError(errorMessage);
      console.error("❌ Error en registro:", errorMessage);
      // El modal sigue abierto para permitir reintentar con otra foto
    } finally {
      setIsSavingFacial(false);
    }
  };

  return (
    <div className="min-h-screen flex transition-all duration-500">
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
          {/* Badge Superior */}
          <div className="absolute top-0 left-0 glass rounded-full px-4 py-2 flex items-center gap-2 animate-float-slow">
            <Sparkles className="w-4 h-4 text-coral" />
            <span className="text-white text-xs font-bold uppercase tracking-wider">Portal Seguro</span>
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

            {/* Navegación */}
            <div className="flex items-center gap-4 mt-8">
              <div className="flex gap-2">
                {slides.map((_, i) => (
                  <div
                    key={i}
                    className={`h-2 rounded-full transition-all duration-500 ${
                      i === currentSlide
                        ? "w-10 bg-coral shadow-[0_0_10px_rgba(255,127,80,0.5)]"
                        : "w-2 bg-white/30"
                    }`}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Círculos decorativos */}
        <div className="absolute -bottom-20 -left-20 w-64 h-64 rounded-full border border-white/10 animate-rotate-slow" />
        <div className="absolute -top-10 -right-10 w-40 h-40 rounded-full border border-coral/20 animate-rotate-slow" style={{ animationDirection: "reverse" }} />
      </div>

      {/* Panel derecho - Formulario */}
      <div className="flex-1 flex items-center justify-center p-8 bg-background overflow-y-auto">
        <div className="w-full max-w-md py-8">
          {/* Botón de volver */}
          <div className="flex items-center gap-2 mb-12 opacity-0 animate-fade-in animation-fill-both">
            <Link to="/" className="flex items-center gap-2 text-coral hover:text-coral/80 transition-colors">
              <ArrowLeft className="w-5 h-5" />
              <span className="font-medium">Volver</span>
            </Link>
          </div>

          {/* Título de registro */}
          <div className="text-center mb-10 opacity-0 animate-fade-in animation-delay-200 animation-fill-both">
            <h1 className="font-display text-4xl md:text-5xl font-bold mb-3">
              Crear <span className="text-coral">Cuenta</span>
            </h1>
            <p className="text-muted-foreground text-lg">
              Únete a nuestra comunidad de usuarios seguros
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
          <form onSubmit={handleRegister} className="space-y-5">
            {/* Nombre Completo */}
            <div className="opacity-0 animate-slide-up animation-delay-300 animation-fill-both">
              <div className="relative group input-glow rounded-xl transition-all duration-300">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground group-focus-within:text-coral transition-colors duration-300" />
                <input
                  type="text"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleInputChange}
                  placeholder="Nombre completo"
                  className="w-full pl-12 pr-4 py-3 bg-secondary border border-border rounded-xl focus:outline-none focus:border-coral transition-all duration-300 text-foreground placeholder:text-muted-foreground"
                  required
                />
              </div>
            </div>

            {/* Email */}
            <div className="opacity-0 animate-slide-up animation-delay-350 animation-fill-both">
              <div className="relative group input-glow rounded-xl transition-all duration-300">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground group-focus-within:text-coral transition-colors duration-300" />
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  placeholder="Email"
                  className="w-full pl-12 pr-4 py-3 bg-secondary border border-border rounded-xl focus:outline-none focus:border-coral transition-all duration-300 text-foreground placeholder:text-muted-foreground"
                  required
                />
              </div>
            </div>

            {/* Username */}
            <div className="opacity-0 animate-slide-up animation-delay-400 animation-fill-both">
              <div className="relative group input-glow rounded-xl transition-all duration-300">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground group-focus-within:text-coral transition-colors duration-300" />
                <input
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleInputChange}
                  placeholder="Nombre de usuario"
                  className="w-full pl-12 pr-4 py-3 bg-secondary border border-border rounded-xl focus:outline-none focus:border-coral transition-all duration-300 text-foreground placeholder:text-muted-foreground"
                  required
                />
              </div>
            </div>

            {/* Contraseña */}
            <div className="opacity-0 animate-slide-up animation-delay-450 animation-fill-both">
              <div className="relative group input-glow rounded-xl transition-all duration-300">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground group-focus-within:text-coral transition-colors duration-300" />
                <input
                  type={showPassword ? "text" : "password"}
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  placeholder="Contraseña"
                  className="w-full pl-12 pr-12 py-3 bg-secondary border border-border rounded-xl focus:outline-none focus:border-coral transition-all duration-300 text-foreground placeholder:text-muted-foreground"
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

              {/* Requisitos de contraseña */}
              {formData.password && (
                <div className="mt-4 p-4 bg-secondary/50 rounded-lg space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    {passwordRequirements.minLength ? (
                      <Check className="w-4 h-4 text-green-500" />
                    ) : (
                      <X className="w-4 h-4 text-gray-400" />
                    )}
                    <span className={passwordRequirements.minLength ? "text-green-500" : "text-muted-foreground"}>
                      Mínimo 8 caracteres
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    {passwordRequirements.hasUppercase ? (
                      <Check className="w-4 h-4 text-green-500" />
                    ) : (
                      <X className="w-4 h-4 text-gray-400" />
                    )}
                    <span className={passwordRequirements.hasUppercase ? "text-green-500" : "text-muted-foreground"}>
                      Una letra mayúscula
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    {passwordRequirements.hasLowercase ? (
                      <Check className="w-4 h-4 text-green-500" />
                    ) : (
                      <X className="w-4 h-4 text-gray-400" />
                    )}
                    <span className={passwordRequirements.hasLowercase ? "text-green-500" : "text-muted-foreground"}>
                      Una letra minúscula
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    {passwordRequirements.hasNumber ? (
                      <Check className="w-4 h-4 text-green-500" />
                    ) : (
                      <X className="w-4 h-4 text-gray-400" />
                    )}
                    <span className={passwordRequirements.hasNumber ? "text-green-500" : "text-muted-foreground"}>
                      Un número
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    {passwordRequirements.hasSpecialChar ? (
                      <Check className="w-4 h-4 text-green-500" />
                    ) : (
                      <X className="w-4 h-4 text-gray-400" />
                    )}
                    <span className={passwordRequirements.hasSpecialChar ? "text-green-500" : "text-muted-foreground"}>
                      Un carácter especial (!@#$%^&*...)
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Confirmar Contraseña */}
            <div className="opacity-0 animate-slide-up animation-delay-500 animation-fill-both">
              <div className="relative group input-glow rounded-xl transition-all duration-300">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground group-focus-within:text-coral transition-colors duration-300" />
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  placeholder="Confirmar contraseña"
                  className="w-full pl-12 pr-12 py-3 bg-secondary border border-border rounded-xl focus:outline-none focus:border-coral transition-all duration-300 text-foreground placeholder:text-muted-foreground"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-coral transition-colors duration-300"
                >
                  {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {formData.confirmPassword && formData.password !== formData.confirmPassword && (
                <p className="text-red-500 text-sm mt-2">Las contraseñas no coinciden</p>
              )}
            </div>

            {/* Botón de Registro */}
            <button
              type="submit"
              disabled={!isFormValid || isLoading}
              className={`w-full py-4 bg-coral text-white rounded-xl font-semibold flex items-center justify-center gap-2 transition-all duration-300 mt-8 opacity-0 animate-slide-up animation-delay-550 animation-fill-both ${
                isFormValid && !isLoading
                  ? "hover:bg-coral-dark hover:scale-[1.02] hover:shadow-lg hover:shadow-coral/30 cursor-pointer"
                  : "opacity-50 cursor-not-allowed"
              }`}
            >
              {isLoading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Registrando...</span>
                </>
              ) : (
                <span>Crear Cuenta</span>
              )}
            </button>
          </form>

          {/* Link de login */}
          <p className="text-center mt-8 text-muted-foreground opacity-0 animate-fade-in animation-delay-600 animation-fill-both">
            ¿Ya tienes cuenta?{" "}
            <Link to="/" className="text-coral font-semibold hover:underline transition-all">
              Inicia sesión
            </Link>
          </p>
        </div>
      </div>

      {/* Modal de Captura Facial - OBLIGATORIO para completar registro */}
      <FacialCaptureModal
        isOpen={showFacialModal}
        onCapture={handleFacialCapture}
        onClose={() => setShowFacialModal(false)}
        isLoading={isSavingFacial}
        mode="capture"
        title="📸 Registro Facial - Paso Obligatorio"
        description="Por favor, mire directamente a la cámara y parpadee 3 veces para completar su registro de forma segura"
      />
    </div>
  );
};

export default RegisterPage;
