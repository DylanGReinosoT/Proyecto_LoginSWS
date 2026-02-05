import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CheckCircle2, PartyPopper, Sparkles, Home, ArrowRight, Mail, User, Calendar, Lock, Zap } from "lucide-react";

interface UserData {
  user_id: string;
  email: string;
  username: string;
  full_name: string;
  is_active: boolean;
  two_factor_enabled: boolean;
  facial_recognition_enabled: boolean;
  created_at: string;
}

const HomePage = () => {
  const navigate = useNavigate();
  const [showContent, setShowContent] = useState(false);
  const [confetti, setConfetti] = useState<Array<{ id: number; left: number; delay: number; color: string }>>([]);
  const [userData, setUserData] = useState<UserData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Mostrar contenido con delay
    setTimeout(() => setShowContent(true), 100);

    // Generar confetti
    const colors = ["#ef5a3c", "#fbbf24", "#34d399", "#60a5fa", "#a78bfa", "#f472b6"];
    const newConfetti = Array.from({ length: 50 }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      delay: Math.random() * 2,
      color: colors[Math.floor(Math.random() * colors.length)],
    }));
    setConfetti(newConfetti);

    // Obtener datos del usuario
    const fetchUserData = async () => {
      try {
        const token = localStorage.getItem("access_token");
        if (!token) {
          navigate("/login");
          return;
        }

        const response = await fetch("http://localhost:8000/api/users/me", {
          method: "GET",
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });

        if (response.ok) {
          const data = await response.json();
          setUserData(data);
        } else if (response.status === 401) {
          navigate("/login");
        }
      } catch (error) {
        console.error("Error fetching user data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, [navigate]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-secondary to-background relative overflow-hidden">
      {/* Confetti */}
      {confetti.map((piece) => (
        <div
          key={piece.id}
          className="absolute top-0 w-3 h-3 rounded-sm animate-confetti"
          style={{
            left: `${piece.left}%`,
            backgroundColor: piece.color,
            animationDelay: `${piece.delay}s`,
          }}
        />
      ))}

      {/* Círculos decorativos de fondo */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-coral/5 blur-3xl animate-float" />
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 rounded-full bg-coral/10 blur-3xl animate-float-slow" />

      {/* Partículas brillantes */}
      {[...Array(15)].map((_, i) => (
        <Sparkles
          key={i}
          className="absolute text-coral/30 animate-twinkle"
          style={{
            top: `${Math.random() * 100}%`,
            left: `${Math.random() * 100}%`,
            width: `${Math.random() * 20 + 10}px`,
            animationDelay: `${Math.random() * 3}s`,
          }}
        />
      ))}

      {/* Contenido principal */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4">
        {/* Icono de éxito */}
        <div
          className={`mb-8 transition-all duration-700 ${
            showContent ? "opacity-100 scale-100" : "opacity-0 scale-0"
          }`}
        >
          <div className="relative">
            <div className="w-32 h-32 rounded-full bg-gradient-to-br from-coral to-coral-dark flex items-center justify-center animate-pulse-glow">
              <CheckCircle2 className="w-16 h-16 text-white animate-success-bounce" />
            </div>
            {/* Anillo giratorio */}
            <div className="absolute inset-0 -m-4 border-4 border-dashed border-coral/30 rounded-full animate-rotate-slow" />
          </div>
        </div>

        {/* Iconos de fiesta */}
        <div
          className={`flex gap-4 mb-6 transition-all duration-700 delay-200 ${
            showContent ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10"
          }`}
        >
          <PartyPopper className="w-8 h-8 text-coral animate-bounce-subtle" />
          <Sparkles className="w-8 h-8 text-coral animate-bounce-subtle animation-delay-200" />
          <PartyPopper className="w-8 h-8 text-coral animate-bounce-subtle animation-delay-400" style={{ transform: "scaleX(-1)" }} />
        </div>

        {/* Título */}
        <h1
          className={`font-display text-5xl md:text-7xl font-bold text-center mb-4 transition-all duration-700 delay-300 ${
            showContent ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10"
          }`}
        >
          <span className="bg-gradient-to-r from-coral via-coral-light to-coral bg-clip-text text-transparent animate-gradient-shift bg-[length:200%_auto]">
            ¡ÉXITO!
          </span>
        </h1>

        {/* Subtítulo */}
        <h2
          className={`font-display text-2xl md:text-4xl text-foreground text-center mb-6 transition-all duration-700 delay-400 ${
            showContent ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10"
          }`}
        >
          Entraste a mi aplicación
        </h2>

        {/* Mensaje */}
        <p
          className={`text-muted-foreground text-lg md:text-xl text-center max-w-md mb-10 transition-all duration-700 delay-500 ${
            showContent ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10"
          }`}
        >
          ¡Bienvenido! Estás listo para explorar un mundo de posibilidades creativas.
        </p>

        {/* Card de perfil del usuario */}
        <div
          className={`bg-card/80 backdrop-blur-sm border border-border rounded-2xl p-8 max-w-2xl w-full shadow-xl transition-all duration-700 delay-600 ${
            showContent ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10"
          }`}
        >
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-coral"></div>
            </div>
          ) : userData ? (
            <>
              {/* Encabezado del perfil */}
              <div className="flex items-start justify-between mb-8 pb-6 border-b border-border">
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-br from-coral to-coral-dark flex items-center justify-center">
                    <User className="w-8 h-8 text-white" />
                  </div>
                  <div>
                    <h3 className="font-display text-2xl font-bold text-foreground">{userData.full_name}</h3>
                    <p className="text-muted-foreground">@{userData.username}</p>
                  </div>
                </div>
                <div className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  userData.is_active 
                    ? "bg-green-100 text-green-700" 
                    : "bg-red-100 text-red-700"
                }`}>
                  {userData.is_active ? "Activo" : "Inactivo"}
                </div>
              </div>

              {/* Información del usuario */}
              <div className="space-y-4">
                {/* Email */}
                <div className="flex items-center gap-4 p-4 rounded-lg bg-secondary hover:bg-muted transition-colors">
                  <Mail className="w-5 h-5 text-coral flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-xs text-muted-foreground uppercase tracking-wide">Email</p>
                    <p className="text-sm font-medium text-foreground break-all">{userData.email}</p>
                  </div>
                </div>

                {/* Usuario ID */}
                <div className="flex items-center gap-4 p-4 rounded-lg bg-secondary hover:bg-muted transition-colors">
                  <User className="w-5 h-5 text-coral flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-xs text-muted-foreground uppercase tracking-wide">ID de Usuario</p>
                    <p className="text-sm font-medium text-foreground font-mono truncate">{userData.user_id}</p>
                  </div>
                </div>

                {/* Fecha de creación */}
                <div className="flex items-center gap-4 p-4 rounded-lg bg-secondary hover:bg-muted transition-colors">
                  <Calendar className="w-5 h-5 text-coral flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-xs text-muted-foreground uppercase tracking-wide">Miembro desde</p>
                    <p className="text-sm font-medium text-foreground">
                      {new Date(userData.created_at).toLocaleDateString("es-ES", {
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  </div>
                </div>

                {/* Seguridad - Dos factores */}
                <div className="flex items-center gap-4 p-4 rounded-lg bg-secondary hover:bg-muted transition-colors">
                  <Lock className="w-5 h-5 text-coral flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-xs text-muted-foreground uppercase tracking-wide">Autenticación en dos pasos</p>
                    <p className={`text-sm font-medium ${userData.two_factor_enabled ? "text-green-600" : "text-yellow-600"}`}>
                      {userData.two_factor_enabled ? "✓ Habilitado" : "○ Deshabilitado"}
                    </p>
                  </div>
                </div>

                {/* Reconocimiento facial */}
                <div className="flex items-center gap-4 p-4 rounded-lg bg-secondary hover:bg-muted transition-colors">
                  <Zap className="w-5 h-5 text-coral flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-xs text-muted-foreground uppercase tracking-wide">Reconocimiento facial</p>
                    <p className={`text-sm font-medium ${userData.facial_recognition_enabled ? "text-green-600" : "text-yellow-600"}`}>
                      {userData.facial_recognition_enabled ? "✓ Habilitado" : "○ Deshabilitado"}
                    </p>
                  </div>
                </div>
              </div>

              {/* Botones de acción */}
              <div className="grid grid-cols-2 gap-4 mt-8 pt-6 border-t border-border">
                <button className="p-4 rounded-xl bg-secondary hover:bg-muted flex items-center justify-between group transition-all duration-300 hover:scale-[1.02]">
                  <span className="font-medium text-foreground">Editar Perfil</span>
                  <ArrowRight className="w-5 h-5 text-muted-foreground group-hover:text-coral group-hover:translate-x-1 transition-all duration-300" />
                </button>
                <button className="p-4 rounded-xl bg-secondary hover:bg-muted flex items-center justify-between group transition-all duration-300 hover:scale-[1.02]">
                  <span className="font-medium text-foreground">Configuración</span>
                  <ArrowRight className="w-5 h-5 text-muted-foreground group-hover:text-coral group-hover:translate-x-1 transition-all duration-300" />
                </button>
              </div>
            </>
          ) : (
            <div className="text-center py-8">
              <p className="text-muted-foreground">No se pudieron cargar los datos del usuario</p>
            </div>
          )}
        </div>

        {/* Botón de cerrar sesión */}
        <button
          onClick={() => {
            localStorage.removeItem("access_token");
            navigate("/login");
          }}
          className={`mt-8 px-8 py-3 rounded-full bg-transparent border-2 border-coral text-coral font-semibold hover:bg-coral hover:text-white transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-coral/30 opacity-0 animate-fade-in animation-delay-800 animation-fill-both`}
        >
          Cerrar sesión
        </button>
      </div>
    </div>
  );
};

export default HomePage;
