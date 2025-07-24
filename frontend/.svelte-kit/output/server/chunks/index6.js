const app = {
  name: "TradeSense",
  tagline: "Negociação Inteligente, Decisões Melhores"
};
const nav = {
  dashboard: "Painel",
  trades: "Registro de Operações",
  portfolio: "Portfólio",
  analytics: "Análises",
  journal: "Diário",
  playbook: "Estratégias",
  aiInsights: "Insights de IA",
  "import": "Importar",
  settings: "Configurações",
  logout: "Sair",
  login: "Entrar",
  register: "Cadastrar-se",
  profile: "Perfil",
  billing: "Faturamento",
  support: "Suporte"
};
const actions$1 = {
  save: "Salvar",
  cancel: "Cancelar",
  "delete": "Excluir",
  edit: "Editar",
  create: "Criar",
  update: "Atualizar",
  submit: "Enviar",
  confirm: "Confirmar",
  back: "Voltar",
  next: "Próximo",
  previous: "Anterior",
  close: "Fechar",
  search: "Pesquisar",
  filter: "Filtrar",
  sort: "Ordenar",
  "export": "Exportar",
  "import": "Importar",
  download: "Baixar",
  upload: "Carregar",
  refresh: "Atualizar",
  retry: "Tentar novamente",
  loading: "Carregando...",
  processing: "Processando..."
};
const status$1 = {
  success: "Sucesso",
  error: "Erro",
  warning: "Aviso",
  info: "Informação",
  pending: "Pendente",
  active: "Ativo",
  inactive: "Inativo",
  online: "Online",
  offline: "Offline",
  connected: "Conectado",
  disconnected: "Desconectado"
};
const time = {
  today: "Hoje",
  yesterday: "Ontem",
  tomorrow: "Amanhã",
  thisWeek: "Esta Semana",
  lastWeek: "Semana Passada",
  thisMonth: "Este Mês",
  lastMonth: "Mês Passado",
  thisYear: "Este Ano",
  lastYear: "Ano Passado",
  custom: "Personalizado",
  from: "De",
  to: "Até",
  date: "Data",
  time: "Hora",
  dateTime: "Data e Hora"
};
const pagination = {
  showing: "Mostrando {{from}} a {{to}} de {{total}}",
  page: "Página {{current}} de {{total}}",
  itemsPerPage: "Itens por página",
  first: "Primeira",
  last: "Última"
};
const errors = {
  general: "Algo deu errado. Por favor, tente novamente.",
  network: "Erro de rede. Por favor, verifique sua conexão.",
  notFound: "Página não encontrada",
  unauthorized: "Você não está autorizado a ver esta página",
  forbidden: "Acesso negado",
  serverError: "Erro no servidor. Por favor, tente novamente mais tarde.",
  timeout: "A solicitação expirou. Por favor, tente novamente."
};
const confirmation = {
  title: "Tem certeza?",
  deleteMessage: "Esta ação não pode ser desfeita.",
  logoutMessage: "Tem certeza que deseja sair?"
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
  title: "Bem-vindo de Volta",
  subtitle: "Entre na sua conta TradeSense",
  email: "E-mail ou Nome de Usuário",
  emailPlaceholder: "Digite seu e-mail ou nome de usuário",
  password: "Senha",
  passwordPlaceholder: "Digite sua senha",
  rememberMe: "Lembrar-me",
  forgotPassword: "Esqueceu a senha?",
  submit: "Entrar",
  submitting: "Entrando...",
  noAccount: "Não tem uma conta?",
  signUp: "Cadastre-se",
  or: "Ou",
  continueWith: "Continuar com {{provider}}",
  errors: {
    invalidCredentials: "E-mail ou senha inválidos",
    accountLocked: "Conta bloqueada. Por favor, entre em contato com o suporte.",
    tooManyAttempts: "Muitas tentativas de login. Por favor, tente novamente mais tarde."
  }
};
const register = {
  title: "Criar Conta",
  subtitle: "Junte-se ao TradeSense e comece a negociar de forma mais inteligente",
  name: "Nome Completo",
  namePlaceholder: "Digite seu nome completo",
  email: "E-mail",
  emailPlaceholder: "Digite seu e-mail",
  username: "Nome de Usuário",
  usernamePlaceholder: "Escolha um nome de usuário",
  password: "Senha",
  passwordPlaceholder: "Crie uma senha",
  confirmPassword: "Confirmar Senha",
  confirmPasswordPlaceholder: "Confirme sua senha",
  terms: "Concordo com os Termos de Serviço e Política de Privacidade",
  submit: "Criar Conta",
  submitting: "Criando conta...",
  hasAccount: "Já tem uma conta?",
  signIn: "Entrar",
  errors: {
    emailTaken: "E-mail já está cadastrado",
    usernameTaken: "Nome de usuário já está em uso",
    weakPassword: "Senha muito fraca",
    passwordMismatch: "As senhas não coincidem"
  }
};
const forgotPassword = {
  title: "Esqueceu a Senha",
  subtitle: "Digite seu e-mail para redefinir sua senha",
  email: "E-mail",
  emailPlaceholder: "Digite seu e-mail",
  submit: "Enviar Link de Redefinição",
  submitting: "Enviando...",
  backToLogin: "Voltar ao login",
  success: "Verifique seu e-mail para instruções de redefinição",
  errors: {
    emailNotFound: "E-mail não encontrado"
  }
};
const resetPassword = {
  title: "Redefinir Senha",
  subtitle: "Crie uma nova senha",
  newPassword: "Nova Senha",
  newPasswordPlaceholder: "Digite a nova senha",
  confirmPassword: "Confirmar Senha",
  confirmPasswordPlaceholder: "Confirme a nova senha",
  submit: "Redefinir Senha",
  submitting: "Redefinindo...",
  success: "Senha redefinida com sucesso",
  errors: {
    invalidToken: "Token de redefinição inválido ou expirado",
    passwordMismatch: "As senhas não coincidem"
  }
};
const changePassword = {
  title: "Alterar Senha",
  currentPassword: "Senha Atual",
  currentPasswordPlaceholder: "Digite a senha atual",
  newPassword: "Nova Senha",
  newPasswordPlaceholder: "Digite a nova senha",
  confirmPassword: "Confirmar Senha",
  confirmPasswordPlaceholder: "Confirme a nova senha",
  submit: "Alterar Senha",
  submitting: "Alterando...",
  success: "Senha alterada com sucesso",
  errors: {
    incorrectPassword: "Senha atual está incorreta",
    samePassword: "A nova senha deve ser diferente"
  }
};
const mfa = {
  title: "Autenticação de Dois Fatores",
  subtitle: "Digite o código do seu aplicativo autenticador",
  code: "Código de Verificação",
  codePlaceholder: "Digite o código de 6 dígitos",
  submit: "Verificar",
  submitting: "Verificando...",
  useBackup: "Usar código de backup",
  errors: {
    invalidCode: "Código de verificação inválido",
    expiredCode: "Código expirado"
  }
};
const logout = {
  message: "Você saiu com sucesso",
  redirect: "Redirecionando para o login..."
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
const required = "{{field}} é obrigatório";
const email = "Por favor, insira um endereço de e-mail válido";
const minLength = "{{field}} deve ter pelo menos {{min}} caracteres";
const maxLength = "{{field}} não deve exceder {{max}} caracteres";
const minValue = "{{field}} deve ser pelo menos {{min}}";
const maxValue = "{{field}} não deve exceder {{max}}";
const pattern = "Formato de {{field}} é inválido";
const passwordStrength = {
  weak: "Senha muito fraca",
  medium: "Força da senha é média",
  strong: "Senha forte"
};
const passwordRequirements = {
  minLength: "Pelo menos 8 caracteres",
  uppercase: "Uma letra maiúscula",
  lowercase: "Uma letra minúscula",
  number: "Um número",
  special: "Um caractere especial"
};
const match = "{{field}} deve corresponder a {{otherField}}";
const unique = "{{field}} deve ser único";
const date = {
  invalid: "Data inválida",
  future: "Data deve estar no futuro",
  past: "Data deve estar no passado",
  between: "Data deve estar entre {{start}} e {{end}}"
};
const number = {
  invalid: "Número inválido",
  integer: "Deve ser um número inteiro",
  positive: "Deve ser um número positivo",
  negative: "Deve ser um número negativo"
};
const file = {
  required: "Por favor, selecione um arquivo",
  size: "Tamanho do arquivo não deve exceder {{max}}",
  type: "Tipo de arquivo inválido. Permitidos: {{types}}"
};
const trades$1 = {
  symbol: "Símbolo é obrigatório",
  quantity: "Quantidade deve ser maior que 0",
  price: "Preço deve ser maior que 0",
  entryPrice: "Preço de entrada é obrigatório",
  exitPrice: "Preço de saída é obrigatório",
  stopLoss: "Stop loss deve ser menor que o preço de entrada",
  takeProfit: "Take profit deve ser maior que o preço de entrada"
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
const title$1 = "Painel";
const welcome = "Bem-vindo de volta, {{name}}!";
const overview = "Visão Geral";
const recentActivity = "Atividade Recente";
const quickActions = "Ações Rápidas";
const metrics = {
  totalTrades: "Total de Operações",
  winRate: "Taxa de Acerto",
  profitLoss: "Lucro/Prejuízo",
  avgReturn: "Retorno Médio",
  totalVolume: "Volume Total",
  activeTrades: "Operações Ativas",
  todaysPL: "L/P de Hoje",
  weeklyPL: "L/P Semanal",
  monthlyPL: "L/P Mensal",
  yearlyPL: "L/P Anual"
};
const charts = {
  performanceOverTime: "Desempenho ao Longo do Tempo",
  profitByStrategy: "Lucro por Estratégia",
  winLossDistribution: "Distribuição de Ganhos/Perdas",
  riskRewardRatio: "Relação Risco/Retorno",
  tradingVolume: "Volume de Negociação",
  topPerformers: "Melhores Desempenhos",
  worstPerformers: "Piores Desempenhos"
};
const widgets = {
  recentTrades: "Operações Recentes",
  upcomingAlerts: "Alertas Próximos",
  marketOverview: "Visão Geral do Mercado",
  newsAndAnalysis: "Notícias e Análises",
  openPositions: "Posições Abertas",
  watchlist: "Lista de Observação"
};
const empty = {
  noData: "Sem dados disponíveis",
  noTrades: "Ainda sem operações. Comece adicionando sua primeira operação!",
  noAlerts: "Sem alertas configurados",
  noPositions: "Sem posições abertas"
};
const timeframes = {
  "1d": "1 Dia",
  "1w": "1 Semana",
  "1m": "1 Mês",
  "3m": "3 Meses",
  "6m": "6 Meses",
  "1y": "1 Ano",
  ytd: "Ano Atual",
  all: "Todo Período"
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
const title = "Registro de Operações";
const newTrade = "Nova Operação";
const editTrade = "Editar Operação";
const deleteTrade = "Excluir Operação";
const importTrades = "Importar Operações";
const exportTrades = "Exportar Operações";
const fields = {
  symbol: "Símbolo",
  side: "Lado",
  quantity: "Quantidade",
  entryPrice: "Preço de Entrada",
  exitPrice: "Preço de Saída",
  entryDate: "Data de Entrada",
  exitDate: "Data de Saída",
  stopLoss: "Stop Loss",
  takeProfit: "Take Profit",
  commission: "Comissão",
  fees: "Taxas",
  notes: "Observações",
  tags: "Tags",
  strategy: "Estratégia",
  status: "Status",
  pnl: "L/P",
  returnPercent: "Retorno %",
  riskReward: "Risco/Retorno"
};
const side = {
  buy: "Compra",
  sell: "Venda",
  long: "Comprado",
  short: "Vendido"
};
const status = {
  open: "Aberta",
  closed: "Fechada",
  pending: "Pendente",
  cancelled: "Cancelada",
  partial: "Parcial"
};
const filters = {
  all: "Todas as Operações",
  open: "Operações Abertas",
  closed: "Operações Fechadas",
  winners: "Vencedoras",
  losers: "Perdedoras",
  today: "Hoje",
  thisWeek: "Esta Semana",
  thisMonth: "Este Mês",
  dateRange: "Período",
  symbol: "Por Símbolo",
  strategy: "Por Estratégia"
};
const actions = {
  view: "Ver Detalhes",
  edit: "Editar",
  "delete": "Excluir",
  duplicate: "Duplicar",
  close: "Fechar Operação",
  addToJournal: "Adicionar ao Diário"
};
const summary = {
  totalTrades: "Total de Operações",
  openTrades: "Operações Abertas",
  closedTrades: "Operações Fechadas",
  totalPnl: "L/P Total",
  winRate: "Taxa de Acerto",
  avgWin: "Ganho Médio",
  avgLoss: "Perda Média",
  profitFactor: "Fator de Lucro"
};
const messages = {
  tradeAdded: "Operação adicionada com sucesso",
  tradeUpdated: "Operação atualizada com sucesso",
  tradeDeleted: "Operação excluída com sucesso",
  tradeClosed: "Operação fechada com sucesso",
  importSuccess: "{{count}} operações importadas com sucesso",
  exportSuccess: "Operações exportadas com sucesso",
  deleteConfirm: "Tem certeza que deseja excluir esta operação?"
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
