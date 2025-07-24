const app = {
  name: "TradeSense",
  tagline: "Trading Inteligente, Mejores Decisiones"
};
const nav = {
  dashboard: "Panel",
  trades: "Registro de Operaciones",
  portfolio: "Cartera",
  analytics: "Análisis",
  journal: "Diario",
  playbook: "Estrategias",
  aiInsights: "Insights IA",
  "import": "Importar",
  settings: "Configuración",
  logout: "Cerrar Sesión",
  login: "Iniciar Sesión",
  register: "Registrarse",
  profile: "Perfil",
  billing: "Facturación",
  support: "Soporte"
};
const actions$1 = {
  save: "Guardar",
  cancel: "Cancelar",
  "delete": "Eliminar",
  edit: "Editar",
  create: "Crear",
  update: "Actualizar",
  submit: "Enviar",
  confirm: "Confirmar",
  back: "Atrás",
  next: "Siguiente",
  previous: "Anterior",
  close: "Cerrar",
  search: "Buscar",
  filter: "Filtrar",
  sort: "Ordenar",
  "export": "Exportar",
  "import": "Importar",
  download: "Descargar",
  upload: "Subir",
  refresh: "Actualizar",
  retry: "Reintentar",
  loading: "Cargando...",
  processing: "Procesando..."
};
const status$1 = {
  success: "Éxito",
  error: "Error",
  warning: "Advertencia",
  info: "Información",
  pending: "Pendiente",
  active: "Activo",
  inactive: "Inactivo",
  online: "En línea",
  offline: "Fuera de línea",
  connected: "Conectado",
  disconnected: "Desconectado"
};
const time = {
  today: "Hoy",
  yesterday: "Ayer",
  tomorrow: "Mañana",
  thisWeek: "Esta Semana",
  lastWeek: "Semana Pasada",
  thisMonth: "Este Mes",
  lastMonth: "Mes Pasado",
  thisYear: "Este Año",
  lastYear: "Año Pasado",
  custom: "Personalizado",
  from: "Desde",
  to: "Hasta",
  date: "Fecha",
  time: "Hora",
  dateTime: "Fecha y Hora"
};
const pagination = {
  showing: "Mostrando {{from}} a {{to}} de {{total}}",
  page: "Página {{current}} de {{total}}",
  itemsPerPage: "Elementos por página",
  first: "Primera",
  last: "Última"
};
const errors = {
  general: "Algo salió mal. Por favor, inténtalo de nuevo.",
  network: "Error de red. Por favor, verifica tu conexión.",
  notFound: "Página no encontrada",
  unauthorized: "No estás autorizado para ver esta página",
  forbidden: "Acceso prohibido",
  serverError: "Error del servidor. Por favor, inténtalo más tarde.",
  timeout: "La solicitud expiró. Por favor, inténtalo de nuevo."
};
const confirmation = {
  title: "¿Estás seguro?",
  deleteMessage: "Esta acción no se puede deshacer.",
  logoutMessage: "¿Estás seguro de que quieres cerrar sesión?"
};
const common = {
  app,
  nav,
  actions: actions$1,
  status: status$1,
  time,
  pagination,
  errors,
  confirmation
};
const login = {
  title: "Bienvenido de Nuevo",
  subtitle: "Inicia sesión en tu cuenta de TradeSense",
  email: "Correo o Usuario",
  emailPlaceholder: "Ingresa tu correo o usuario",
  password: "Contraseña",
  passwordPlaceholder: "Ingresa tu contraseña",
  rememberMe: "Recuérdame",
  forgotPassword: "¿Olvidaste tu contraseña?",
  submit: "Iniciar Sesión",
  submitting: "Iniciando sesión...",
  noAccount: "¿No tienes una cuenta?",
  signUp: "Regístrate",
  or: "O",
  continueWith: "Continuar con {{provider}}",
  errors: {
    invalidCredentials: "Correo o contraseña inválidos",
    accountLocked: "La cuenta está bloqueada. Por favor, contacta soporte.",
    tooManyAttempts: "Demasiados intentos de inicio de sesión. Por favor, inténtalo más tarde."
  }
};
const register = {
  title: "Crear Cuenta",
  subtitle: "Únete a TradeSense y comienza a operar más inteligentemente",
  name: "Nombre Completo",
  namePlaceholder: "Ingresa tu nombre completo",
  email: "Correo Electrónico",
  emailPlaceholder: "Ingresa tu correo",
  username: "Usuario",
  usernamePlaceholder: "Elige un nombre de usuario",
  password: "Contraseña",
  passwordPlaceholder: "Crea una contraseña",
  confirmPassword: "Confirmar Contraseña",
  confirmPasswordPlaceholder: "Confirma tu contraseña",
  terms: "Acepto los Términos de Servicio y la Política de Privacidad",
  submit: "Crear Cuenta",
  submitting: "Creando cuenta...",
  hasAccount: "¿Ya tienes una cuenta?",
  signIn: "Inicia sesión",
  errors: {
    emailTaken: "El correo ya está registrado",
    usernameTaken: "El nombre de usuario ya está en uso",
    weakPassword: "La contraseña es muy débil",
    passwordMismatch: "Las contraseñas no coinciden"
  }
};
const forgotPassword = {
  title: "Olvidé mi Contraseña",
  subtitle: "Ingresa tu correo para restablecer tu contraseña",
  email: "Correo Electrónico",
  emailPlaceholder: "Ingresa tu correo",
  submit: "Enviar Enlace",
  submitting: "Enviando...",
  backToLogin: "Volver a iniciar sesión",
  success: "Revisa tu correo para las instrucciones de restablecimiento",
  errors: {
    emailNotFound: "Correo no encontrado"
  }
};
const resetPassword = {
  title: "Restablecer Contraseña",
  subtitle: "Crea una nueva contraseña",
  newPassword: "Nueva Contraseña",
  newPasswordPlaceholder: "Ingresa nueva contraseña",
  confirmPassword: "Confirmar Contraseña",
  confirmPasswordPlaceholder: "Confirma nueva contraseña",
  submit: "Restablecer Contraseña",
  submitting: "Restableciendo...",
  success: "Contraseña restablecida exitosamente",
  errors: {
    invalidToken: "Token inválido o expirado",
    passwordMismatch: "Las contraseñas no coinciden"
  }
};
const changePassword = {
  title: "Cambiar Contraseña",
  currentPassword: "Contraseña Actual",
  currentPasswordPlaceholder: "Ingresa contraseña actual",
  newPassword: "Nueva Contraseña",
  newPasswordPlaceholder: "Ingresa nueva contraseña",
  confirmPassword: "Confirmar Contraseña",
  confirmPasswordPlaceholder: "Confirma nueva contraseña",
  submit: "Cambiar Contraseña",
  submitting: "Cambiando...",
  success: "Contraseña cambiada exitosamente",
  errors: {
    incorrectPassword: "La contraseña actual es incorrecta",
    samePassword: "La nueva contraseña debe ser diferente"
  }
};
const mfa = {
  title: "Autenticación de Dos Factores",
  subtitle: "Ingresa el código de tu aplicación de autenticación",
  code: "Código de Verificación",
  codePlaceholder: "Ingresa código de 6 dígitos",
  submit: "Verificar",
  submitting: "Verificando...",
  useBackup: "Usar código de respaldo",
  errors: {
    invalidCode: "Código de verificación inválido",
    expiredCode: "El código ha expirado"
  }
};
const logout = {
  message: "Has cerrado sesión exitosamente",
  redirect: "Redirigiendo al inicio de sesión..."
};
const auth = {
  login,
  register,
  forgotPassword,
  resetPassword,
  changePassword,
  mfa,
  logout
};
const required = "{{field}} es requerido";
const email = "Por favor ingresa un correo electrónico válido";
const minLength = "{{field}} debe tener al menos {{min}} caracteres";
const maxLength = "{{field}} no debe exceder {{max}} caracteres";
const minValue = "{{field}} debe ser al menos {{min}}";
const maxValue = "{{field}} no debe exceder {{max}}";
const pattern = "El formato de {{field}} es inválido";
const passwordStrength = {
  weak: "La contraseña es muy débil",
  medium: "La fortaleza de la contraseña es media",
  strong: "La contraseña es fuerte"
};
const passwordRequirements = {
  minLength: "Al menos 8 caracteres",
  uppercase: "Una letra mayúscula",
  lowercase: "Una letra minúscula",
  number: "Un número",
  special: "Un carácter especial"
};
const match = "{{field}} debe coincidir con {{otherField}}";
const unique = "{{field}} debe ser único";
const date = {
  invalid: "Fecha inválida",
  future: "La fecha debe estar en el futuro",
  past: "La fecha debe estar en el pasado",
  between: "La fecha debe estar entre {{start}} y {{end}}"
};
const number = {
  invalid: "Número inválido",
  integer: "Debe ser un número entero",
  positive: "Debe ser un número positivo",
  negative: "Debe ser un número negativo"
};
const file = {
  required: "Por favor selecciona un archivo",
  size: "El tamaño del archivo no debe exceder {{max}}",
  type: "Tipo de archivo inválido. Permitidos: {{types}}"
};
const trades$1 = {
  symbol: "El símbolo es requerido",
  quantity: "La cantidad debe ser mayor que 0",
  price: "El precio debe ser mayor que 0",
  entryPrice: "El precio de entrada es requerido",
  exitPrice: "El precio de salida es requerido",
  stopLoss: "El stop loss debe ser menor que el precio de entrada",
  takeProfit: "El take profit debe ser mayor que el precio de entrada"
};
const validation = {
  required,
  email,
  minLength,
  maxLength,
  minValue,
  maxValue,
  pattern,
  passwordStrength,
  passwordRequirements,
  match,
  unique,
  date,
  number,
  file,
  trades: trades$1
};
const title$1 = "Panel de Control";
const welcome = "¡Bienvenido de nuevo, {{name}}!";
const overview = "Resumen";
const recentActivity = "Actividad Reciente";
const quickActions = "Acciones Rápidas";
const metrics = {
  totalTrades: "Total de Operaciones",
  winRate: "Tasa de Éxito",
  profitLoss: "Ganancia/Pérdida",
  avgReturn: "Retorno Promedio",
  totalVolume: "Volumen Total",
  activeTrades: "Operaciones Activas",
  todaysPL: "P/G de Hoy",
  weeklyPL: "P/G Semanal",
  monthlyPL: "P/G Mensual",
  yearlyPL: "P/G Anual"
};
const charts = {
  performanceOverTime: "Rendimiento a lo Largo del Tiempo",
  profitByStrategy: "Ganancia por Estrategia",
  winLossDistribution: "Distribución de Ganancias/Pérdidas",
  riskRewardRatio: "Ratio Riesgo/Recompensa",
  tradingVolume: "Volumen de Trading",
  topPerformers: "Mejores Rendimientos",
  worstPerformers: "Peores Rendimientos"
};
const widgets = {
  recentTrades: "Operaciones Recientes",
  upcomingAlerts: "Alertas Próximas",
  marketOverview: "Resumen del Mercado",
  newsAndAnalysis: "Noticias y Análisis",
  openPositions: "Posiciones Abiertas",
  watchlist: "Lista de Seguimiento"
};
const empty = {
  noData: "No hay datos disponibles",
  noTrades: "No hay operaciones aún. ¡Comienza agregando tu primera operación!",
  noAlerts: "No hay alertas configuradas",
  noPositions: "No hay posiciones abiertas"
};
const timeframes = {
  "1d": "1 Día",
  "1w": "1 Semana",
  "1m": "1 Mes",
  "3m": "3 Meses",
  "6m": "6 Meses",
  "1y": "1 Año",
  ytd: "YTD",
  all: "Todo el Tiempo"
};
const dashboard = {
  title: title$1,
  welcome,
  overview,
  recentActivity,
  quickActions,
  metrics,
  charts,
  widgets,
  empty,
  timeframes
};
const title = "Registro de Operaciones";
const newTrade = "Nueva Operación";
const editTrade = "Editar Operación";
const deleteTrade = "Eliminar Operación";
const importTrades = "Importar Operaciones";
const exportTrades = "Exportar Operaciones";
const fields = {
  symbol: "Símbolo",
  side: "Lado",
  quantity: "Cantidad",
  entryPrice: "Precio de Entrada",
  exitPrice: "Precio de Salida",
  entryDate: "Fecha de Entrada",
  exitDate: "Fecha de Salida",
  stopLoss: "Stop Loss",
  takeProfit: "Take Profit",
  commission: "Comisión",
  fees: "Tarifas",
  notes: "Notas",
  tags: "Etiquetas",
  strategy: "Estrategia",
  status: "Estado",
  pnl: "P&G",
  returnPercent: "Retorno %",
  riskReward: "Riesgo/Recompensa"
};
const side = {
  buy: "Compra",
  sell: "Venta",
  long: "Largo",
  short: "Corto"
};
const status = {
  open: "Abierta",
  closed: "Cerrada",
  pending: "Pendiente",
  cancelled: "Cancelada",
  partial: "Parcial"
};
const filters = {
  all: "Todas las Operaciones",
  open: "Operaciones Abiertas",
  closed: "Operaciones Cerradas",
  winners: "Ganadoras",
  losers: "Perdedoras",
  today: "Hoy",
  thisWeek: "Esta Semana",
  thisMonth: "Este Mes",
  dateRange: "Rango de Fechas",
  symbol: "Por Símbolo",
  strategy: "Por Estrategia"
};
const actions = {
  view: "Ver Detalles",
  edit: "Editar",
  "delete": "Eliminar",
  duplicate: "Duplicar",
  close: "Cerrar Operación",
  addToJournal: "Agregar al Diario"
};
const summary = {
  totalTrades: "Total de Operaciones",
  openTrades: "Operaciones Abiertas",
  closedTrades: "Operaciones Cerradas",
  totalPnl: "P&G Total",
  winRate: "Tasa de Éxito",
  avgWin: "Ganancia Promedio",
  avgLoss: "Pérdida Promedio",
  profitFactor: "Factor de Ganancia"
};
const messages = {
  tradeAdded: "Operación agregada exitosamente",
  tradeUpdated: "Operación actualizada exitosamente",
  tradeDeleted: "Operación eliminada exitosamente",
  tradeClosed: "Operación cerrada exitosamente",
  importSuccess: "{{count}} operaciones importadas exitosamente",
  exportSuccess: "Operaciones exportadas exitosamente",
  deleteConfirm: "¿Estás seguro de que quieres eliminar esta operación?"
};
const trades = {
  title,
  newTrade,
  editTrade,
  deleteTrade,
  importTrades,
  exportTrades,
  fields,
  side,
  status,
  filters,
  actions,
  summary,
  messages
};
const index = {
  common,
  auth,
  validation,
  dashboard,
  trades
};
export {
  index as default
};
