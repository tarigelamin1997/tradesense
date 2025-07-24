const app = {
  name: "TradeSense",
  tagline: "Trading Cerdas, Keputusan Lebih Baik"
};
const nav = {
  dashboard: "Dasbor",
  trades: "Log Perdagangan",
  portfolio: "Portofolio",
  analytics: "Analitik",
  journal: "Jurnal",
  playbook: "Panduan Strategi",
  aiInsights: "Wawasan AI",
  "import": "Impor",
  settings: "Pengaturan",
  logout: "Keluar",
  login: "Masuk",
  register: "Daftar",
  profile: "Profil",
  billing: "Tagihan",
  support: "Dukungan"
};
const actions$1 = {
  save: "Simpan",
  cancel: "Batal",
  "delete": "Hapus",
  edit: "Ubah",
  create: "Buat",
  update: "Perbarui",
  submit: "Kirim",
  confirm: "Konfirmasi",
  back: "Kembali",
  next: "Selanjutnya",
  previous: "Sebelumnya",
  close: "Tutup",
  search: "Cari",
  filter: "Filter",
  sort: "Urutkan",
  "export": "Ekspor",
  "import": "Impor",
  download: "Unduh",
  upload: "Unggah",
  refresh: "Segarkan",
  retry: "Coba Lagi",
  loading: "Memuat...",
  processing: "Memproses..."
};
const status$1 = {
  success: "Berhasil",
  error: "Kesalahan",
  warning: "Peringatan",
  info: "Informasi",
  pending: "Tertunda",
  active: "Aktif",
  inactive: "Tidak Aktif",
  online: "Daring",
  offline: "Luring",
  connected: "Terhubung",
  disconnected: "Terputus"
};
const time = {
  today: "Hari Ini",
  yesterday: "Kemarin",
  tomorrow: "Besok",
  thisWeek: "Minggu Ini",
  lastWeek: "Minggu Lalu",
  thisMonth: "Bulan Ini",
  lastMonth: "Bulan Lalu",
  thisYear: "Tahun Ini",
  lastYear: "Tahun Lalu",
  custom: "Kustom",
  from: "Dari",
  to: "Hingga",
  date: "Tanggal",
  time: "Waktu",
  dateTime: "Tanggal & Waktu"
};
const pagination = {
  showing: "Menampilkan {{from}} hingga {{to}} dari {{total}}",
  page: "Halaman {{current}} dari {{total}}",
  itemsPerPage: "Item per halaman",
  first: "Pertama",
  last: "Terakhir"
};
const errors = {
  general: "Terjadi kesalahan. Silakan coba lagi.",
  network: "Kesalahan jaringan. Periksa koneksi Anda.",
  notFound: "Halaman tidak ditemukan",
  unauthorized: "Anda tidak memiliki izin untuk melihat halaman ini",
  forbidden: "Akses ditolak",
  serverError: "Kesalahan server. Silakan coba lagi nanti.",
  timeout: "Permintaan habis waktu. Silakan coba lagi."
};
const confirmation = {
  title: "Apakah Anda yakin?",
  deleteMessage: "Tindakan ini tidak dapat dibatalkan.",
  logoutMessage: "Apakah Anda yakin ingin keluar?"
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
  title: "Selamat Datang Kembali",
  subtitle: "Masuk ke akun TradeSense Anda",
  email: "Email atau Nama Pengguna",
  emailPlaceholder: "Masukkan email atau nama pengguna Anda",
  password: "Kata Sandi",
  passwordPlaceholder: "Masukkan kata sandi Anda",
  rememberMe: "Ingat saya",
  forgotPassword: "Lupa kata sandi?",
  submit: "Masuk",
  submitting: "Sedang masuk...",
  noAccount: "Belum punya akun?",
  signUp: "Daftar",
  or: "Atau",
  continueWith: "Lanjutkan dengan {{provider}}",
  errors: {
    invalidCredentials: "Email atau kata sandi tidak valid",
    accountLocked: "Akun terkunci. Silakan hubungi dukungan.",
    tooManyAttempts: "Terlalu banyak percobaan masuk. Silakan coba lagi nanti."
  }
};
const register = {
  title: "Buat Akun",
  subtitle: "Bergabunglah dengan TradeSense dan mulai trading lebih cerdas",
  name: "Nama Lengkap",
  namePlaceholder: "Masukkan nama lengkap Anda",
  email: "Email",
  emailPlaceholder: "Masukkan email Anda",
  username: "Nama Pengguna",
  usernamePlaceholder: "Pilih nama pengguna",
  password: "Kata Sandi",
  passwordPlaceholder: "Buat kata sandi",
  confirmPassword: "Konfirmasi Kata Sandi",
  confirmPasswordPlaceholder: "Konfirmasi kata sandi Anda",
  terms: "Saya menyetujui Ketentuan Layanan dan Kebijakan Privasi",
  submit: "Buat Akun",
  submitting: "Membuat akun...",
  hasAccount: "Sudah punya akun?",
  signIn: "Masuk",
  errors: {
    emailTaken: "Email sudah terdaftar",
    usernameTaken: "Nama pengguna sudah digunakan",
    weakPassword: "Kata sandi terlalu lemah",
    passwordMismatch: "Kata sandi tidak cocok"
  }
};
const forgotPassword = {
  title: "Lupa Kata Sandi",
  subtitle: "Masukkan email Anda untuk mereset kata sandi",
  email: "Email",
  emailPlaceholder: "Masukkan email Anda",
  submit: "Kirim Tautan Reset",
  submitting: "Mengirim...",
  backToLogin: "Kembali ke halaman masuk",
  success: "Periksa email Anda untuk instruksi reset",
  errors: {
    emailNotFound: "Email tidak ditemukan"
  }
};
const resetPassword = {
  title: "Reset Kata Sandi",
  subtitle: "Buat kata sandi baru",
  newPassword: "Kata Sandi Baru",
  newPasswordPlaceholder: "Masukkan kata sandi baru",
  confirmPassword: "Konfirmasi Kata Sandi",
  confirmPasswordPlaceholder: "Konfirmasi kata sandi baru",
  submit: "Reset Kata Sandi",
  submitting: "Mereset...",
  success: "Kata sandi berhasil direset",
  errors: {
    invalidToken: "Token reset tidak valid atau sudah kedaluwarsa",
    passwordMismatch: "Kata sandi tidak cocok"
  }
};
const changePassword = {
  title: "Ubah Kata Sandi",
  currentPassword: "Kata Sandi Saat Ini",
  currentPasswordPlaceholder: "Masukkan kata sandi saat ini",
  newPassword: "Kata Sandi Baru",
  newPasswordPlaceholder: "Masukkan kata sandi baru",
  confirmPassword: "Konfirmasi Kata Sandi",
  confirmPasswordPlaceholder: "Konfirmasi kata sandi baru",
  submit: "Ubah Kata Sandi",
  submitting: "Mengubah...",
  success: "Kata sandi berhasil diubah",
  errors: {
    incorrectPassword: "Kata sandi saat ini tidak benar",
    samePassword: "Kata sandi baru harus berbeda"
  }
};
const mfa = {
  title: "Autentikasi Dua Faktor",
  subtitle: "Masukkan kode dari aplikasi autentikator Anda",
  code: "Kode Verifikasi",
  codePlaceholder: "Masukkan kode 6 digit",
  submit: "Verifikasi",
  submitting: "Memverifikasi...",
  useBackup: "Gunakan kode cadangan",
  errors: {
    invalidCode: "Kode verifikasi tidak valid",
    expiredCode: "Kode sudah kedaluwarsa"
  }
};
const logout = {
  message: "Anda telah berhasil keluar",
  redirect: "Mengalihkan ke halaman masuk..."
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
const required = "{{field}} wajib diisi";
const email = "Silakan masukkan alamat email yang valid";
const minLength = "{{field}} harus memiliki minimal {{min}} karakter";
const maxLength = "{{field}} tidak boleh melebihi {{max}} karakter";
const minValue = "{{field}} harus minimal {{min}}";
const maxValue = "{{field}} tidak boleh melebihi {{max}}";
const pattern = "Format {{field}} tidak valid";
const passwordStrength = {
  weak: "Kata sandi terlalu lemah",
  medium: "Kekuatan kata sandi sedang",
  strong: "Kata sandi kuat"
};
const passwordRequirements = {
  minLength: "Minimal 8 karakter",
  uppercase: "Satu huruf kapital",
  lowercase: "Satu huruf kecil",
  number: "Satu angka",
  special: "Satu karakter khusus"
};
const match = "{{field}} harus cocok dengan {{otherField}}";
const unique = "{{field}} harus unik";
const date = {
  invalid: "Tanggal tidak valid",
  future: "Tanggal harus di masa depan",
  past: "Tanggal harus di masa lalu",
  between: "Tanggal harus antara {{start}} dan {{end}}"
};
const number = {
  invalid: "Angka tidak valid",
  integer: "Harus berupa bilangan bulat",
  positive: "Harus berupa angka positif",
  negative: "Harus berupa angka negatif"
};
const file = {
  required: "Silakan pilih file",
  size: "Ukuran file tidak boleh melebihi {{max}}",
  type: "Jenis file tidak valid. Diperbolehkan: {{types}}"
};
const trades$1 = {
  symbol: "Simbol wajib diisi",
  quantity: "Kuantitas harus lebih dari 0",
  price: "Harga harus lebih dari 0",
  entryPrice: "Harga masuk wajib diisi",
  exitPrice: "Harga keluar wajib diisi",
  stopLoss: "Stop loss harus kurang dari harga masuk",
  takeProfit: "Take profit harus lebih dari harga masuk"
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
const title$1 = "Dasbor";
const welcome = "Selamat datang kembali, {{name}}!";
const overview = "Ringkasan";
const recentActivity = "Aktivitas Terkini";
const quickActions = "Aksi Cepat";
const metrics = {
  totalTrades: "Total Perdagangan",
  winRate: "Tingkat Kemenangan",
  profitLoss: "Untung/Rugi",
  avgReturn: "Return Rata-rata",
  totalVolume: "Volume Total",
  activeTrades: "Perdagangan Aktif",
  todaysPL: "U/R Hari Ini",
  weeklyPL: "U/R Mingguan",
  monthlyPL: "U/R Bulanan",
  yearlyPL: "U/R Tahunan"
};
const charts = {
  performanceOverTime: "Performa Sepanjang Waktu",
  profitByStrategy: "Profit per Strategi",
  winLossDistribution: "Distribusi Menang/Kalah",
  riskRewardRatio: "Rasio Risiko/Imbalan",
  tradingVolume: "Volume Perdagangan",
  topPerformers: "Performa Terbaik",
  worstPerformers: "Performa Terburuk"
};
const widgets = {
  recentTrades: "Perdagangan Terkini",
  upcomingAlerts: "Peringatan Mendatang",
  marketOverview: "Ikhtisar Pasar",
  newsAndAnalysis: "Berita & Analisis",
  openPositions: "Posisi Terbuka",
  watchlist: "Daftar Pantau"
};
const empty = {
  noData: "Tidak ada data tersedia",
  noTrades: "Belum ada perdagangan. Mulailah dengan menambahkan perdagangan pertama Anda!",
  noAlerts: "Tidak ada peringatan yang ditetapkan",
  noPositions: "Tidak ada posisi terbuka"
};
const timeframes = {
  "1d": "1 Hari",
  "1w": "1 Minggu",
  "1m": "1 Bulan",
  "3m": "3 Bulan",
  "6m": "6 Bulan",
  "1y": "1 Tahun",
  ytd: "YTD",
  all: "Sepanjang Waktu"
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
const title = "Log Perdagangan";
const newTrade = "Perdagangan Baru";
const editTrade = "Edit Perdagangan";
const deleteTrade = "Hapus Perdagangan";
const importTrades = "Impor Perdagangan";
const exportTrades = "Ekspor Perdagangan";
const fields = {
  symbol: "Simbol",
  side: "Sisi",
  quantity: "Kuantitas",
  entryPrice: "Harga Masuk",
  exitPrice: "Harga Keluar",
  entryDate: "Tanggal Masuk",
  exitDate: "Tanggal Keluar",
  stopLoss: "Stop Loss",
  takeProfit: "Take Profit",
  commission: "Komisi",
  fees: "Biaya",
  notes: "Catatan",
  tags: "Tag",
  strategy: "Strategi",
  status: "Status",
  pnl: "U&R",
  returnPercent: "Return %",
  riskReward: "Risiko/Imbalan"
};
const side = {
  buy: "Beli",
  sell: "Jual",
  long: "Long",
  short: "Short"
};
const status = {
  open: "Terbuka",
  closed: "Ditutup",
  pending: "Tertunda",
  cancelled: "Dibatalkan",
  partial: "Parsial"
};
const filters = {
  all: "Semua Perdagangan",
  open: "Perdagangan Terbuka",
  closed: "Perdagangan Tertutup",
  winners: "Menang",
  losers: "Kalah",
  today: "Hari Ini",
  thisWeek: "Minggu Ini",
  thisMonth: "Bulan Ini",
  dateRange: "Rentang Tanggal",
  symbol: "Berdasarkan Simbol",
  strategy: "Berdasarkan Strategi"
};
const actions = {
  view: "Lihat Detail",
  edit: "Edit",
  "delete": "Hapus",
  duplicate: "Duplikat",
  close: "Tutup Perdagangan",
  addToJournal: "Tambah ke Jurnal"
};
const summary = {
  totalTrades: "Total Perdagangan",
  openTrades: "Perdagangan Terbuka",
  closedTrades: "Perdagangan Tertutup",
  totalPnl: "Total U&R",
  winRate: "Tingkat Kemenangan",
  avgWin: "Rata-rata Menang",
  avgLoss: "Rata-rata Kalah",
  profitFactor: "Faktor Profit"
};
const messages = {
  tradeAdded: "Perdagangan berhasil ditambahkan",
  tradeUpdated: "Perdagangan berhasil diperbarui",
  tradeDeleted: "Perdagangan berhasil dihapus",
  tradeClosed: "Perdagangan berhasil ditutup",
  importSuccess: "{{count}} perdagangan berhasil diimpor",
  exportSuccess: "Perdagangan berhasil diekspor",
  deleteConfirm: "Apakah Anda yakin ingin menghapus perdagangan ini?"
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
