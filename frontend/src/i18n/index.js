/**
 * Internationalization (i18n) Support
 * Multi-language UI for Good Shepherd
 */

// Supported languages
export const LANGUAGES = {
  en: { name: 'English', nativeName: 'English', dir: 'ltr' },
  es: { name: 'Spanish', nativeName: 'Español', dir: 'ltr' },
  fr: { name: 'French', nativeName: 'Français', dir: 'ltr' },
  ar: { name: 'Arabic', nativeName: 'العربية', dir: 'rtl' },
  zh: { name: 'Chinese', nativeName: '中文', dir: 'ltr' },
  pt: { name: 'Portuguese', nativeName: 'Português', dir: 'ltr' },
  ru: { name: 'Russian', nativeName: 'Русский', dir: 'ltr' },
  sw: { name: 'Swahili', nativeName: 'Kiswahili', dir: 'ltr' },
};

// Translation strings
const translations = {
  en: {
    // Common
    app_name: 'Good Shepherd',
    loading: 'Loading...',
    error: 'Error',
    success: 'Success',
    cancel: 'Cancel',
    save: 'Save',
    close: 'Close',
    retry: 'Retry',
    
    // Connection status
    online: 'Online',
    offline: 'Offline',
    offline_notice: "You're offline. Data will sync when connected.",
    
    // Check-in
    checkin_title: 'Safety Check-In',
    checkin_subtitle: 'Let your team know you\'re okay',
    checkin_safe: "I'm Safe",
    checkin_caution: 'Caution',
    checkin_help: 'Need Help',
    checkin_send: 'Send Check-In',
    checkin_success: 'Check-In Recorded',
    checkin_synced: 'Your status has been sent to your coordinator.',
    checkin_pending: "Your check-in will be synced when you're back online.",
    checkin_last: 'Last check-in',
    checkin_add_note: 'Add a note (optional)',
    
    // Alerts
    alerts: 'Alerts',
    no_alerts: 'No critical alerts in your region',
    unacknowledged: 'Unacknowledged Alerts',
    recent_events: 'Recent High-Priority Events',
    got_it: 'Got it',
    
    // Daily brief
    daily_brief: 'Daily Brief',
    critical: 'Critical',
    high: 'High',
    medium: 'Medium',
    low: 'Low',
    total: 'Total',
    monitoring: 'Monitoring',
    
    // Contacts
    emergency_contacts: 'Emergency Contacts',
    emergency_line: 'Emergency Line',
    regional_coordinator: 'Regional Coordinator',
    local_embassy: 'Local Embassy',
    
    // Navigation
    nav_alerts: 'Alerts',
    nav_brief: 'Brief',
    nav_contacts: 'Contacts',
    nav_settings: 'Settings',
    
    // Settings
    settings: 'Settings',
    language: 'Language',
    notifications: 'Notifications',
    push_notifications: 'Push Notifications',
    sms_fallback: 'SMS Fallback',
    region_settings: 'Region Settings',
    your_region: 'Your Region',
    offline_data: 'Offline Data',
    clear_cache: 'Clear Cache',
    storage_used: 'Storage Used',
    
    // Threat levels
    threat_critical: 'Critical Threat',
    threat_high: 'High Threat',
    threat_medium: 'Medium Threat',
    threat_low: 'Low Threat',
    threat_minimal: 'Minimal Threat',
    
    // Location
    location: 'Location',
    getting_location: 'Getting location...',
    location_unavailable: 'Location unavailable',
    
    // Time
    just_now: 'Just now',
    hours_ago: '{n}h ago',
    days_ago: '{n}d ago',
  },
  
  es: {
    app_name: 'Good Shepherd',
    loading: 'Cargando...',
    error: 'Error',
    success: 'Éxito',
    cancel: 'Cancelar',
    save: 'Guardar',
    close: 'Cerrar',
    retry: 'Reintentar',
    
    online: 'En línea',
    offline: 'Sin conexión',
    offline_notice: 'Estás sin conexión. Los datos se sincronizarán cuando te conectes.',
    
    checkin_title: 'Registro de Seguridad',
    checkin_subtitle: 'Informa a tu equipo que estás bien',
    checkin_safe: 'Estoy Bien',
    checkin_caution: 'Precaución',
    checkin_help: 'Necesito Ayuda',
    checkin_send: 'Enviar Registro',
    checkin_success: 'Registro Guardado',
    checkin_synced: 'Tu estado ha sido enviado a tu coordinador.',
    checkin_pending: 'Tu registro se sincronizará cuando vuelvas a conectarte.',
    checkin_last: 'Último registro',
    checkin_add_note: 'Agregar nota (opcional)',
    
    alerts: 'Alertas',
    no_alerts: 'No hay alertas críticas en tu región',
    unacknowledged: 'Alertas Sin Confirmar',
    recent_events: 'Eventos Recientes de Alta Prioridad',
    got_it: 'Entendido',
    
    daily_brief: 'Resumen Diario',
    critical: 'Crítico',
    high: 'Alto',
    medium: 'Medio',
    low: 'Bajo',
    total: 'Total',
    monitoring: 'Monitoreando',
    
    emergency_contacts: 'Contactos de Emergencia',
    emergency_line: 'Línea de Emergencia',
    regional_coordinator: 'Coordinador Regional',
    local_embassy: 'Embajada Local',
    
    nav_alerts: 'Alertas',
    nav_brief: 'Resumen',
    nav_contacts: 'Contactos',
    nav_settings: 'Ajustes',
    
    settings: 'Ajustes',
    language: 'Idioma',
    notifications: 'Notificaciones',
    push_notifications: 'Notificaciones Push',
    sms_fallback: 'SMS de Respaldo',
    region_settings: 'Configuración de Región',
    your_region: 'Tu Región',
    offline_data: 'Datos Sin Conexión',
    clear_cache: 'Limpiar Caché',
    storage_used: 'Almacenamiento Usado',
    
    threat_critical: 'Amenaza Crítica',
    threat_high: 'Amenaza Alta',
    threat_medium: 'Amenaza Media',
    threat_low: 'Amenaza Baja',
    threat_minimal: 'Amenaza Mínima',
    
    location: 'Ubicación',
    getting_location: 'Obteniendo ubicación...',
    location_unavailable: 'Ubicación no disponible',
    
    just_now: 'Ahora mismo',
    hours_ago: 'hace {n}h',
    days_ago: 'hace {n}d',
  },
  
  fr: {
    app_name: 'Good Shepherd',
    loading: 'Chargement...',
    error: 'Erreur',
    success: 'Succès',
    cancel: 'Annuler',
    save: 'Enregistrer',
    close: 'Fermer',
    retry: 'Réessayer',
    
    online: 'En ligne',
    offline: 'Hors ligne',
    offline_notice: 'Vous êtes hors ligne. Les données seront synchronisées une fois connecté.',
    
    checkin_title: 'Pointage de Sécurité',
    checkin_subtitle: 'Informez votre équipe que vous allez bien',
    checkin_safe: 'Je vais bien',
    checkin_caution: 'Prudence',
    checkin_help: "Besoin d'aide",
    checkin_send: 'Envoyer le Pointage',
    checkin_success: 'Pointage Enregistré',
    checkin_synced: 'Votre statut a été envoyé à votre coordinateur.',
    checkin_pending: 'Votre pointage sera synchronisé lorsque vous serez reconnecté.',
    checkin_last: 'Dernier pointage',
    checkin_add_note: 'Ajouter une note (optionnel)',
    
    alerts: 'Alertes',
    no_alerts: 'Aucune alerte critique dans votre région',
    unacknowledged: 'Alertes Non Confirmées',
    recent_events: 'Événements Récents Prioritaires',
    got_it: 'Compris',
    
    daily_brief: 'Briefing Quotidien',
    critical: 'Critique',
    high: 'Élevé',
    medium: 'Moyen',
    low: 'Faible',
    total: 'Total',
    monitoring: 'Surveillance',
    
    emergency_contacts: "Contacts d'Urgence",
    emergency_line: "Ligne d'Urgence",
    regional_coordinator: 'Coordinateur Régional',
    local_embassy: 'Ambassade Locale',
    
    nav_alerts: 'Alertes',
    nav_brief: 'Briefing',
    nav_contacts: 'Contacts',
    nav_settings: 'Paramètres',
    
    settings: 'Paramètres',
    language: 'Langue',
    notifications: 'Notifications',
    push_notifications: 'Notifications Push',
    sms_fallback: 'SMS de Secours',
    region_settings: 'Paramètres de Région',
    your_region: 'Votre Région',
    offline_data: 'Données Hors Ligne',
    clear_cache: 'Vider le Cache',
    storage_used: 'Stockage Utilisé',
    
    threat_critical: 'Menace Critique',
    threat_high: 'Menace Élevée',
    threat_medium: 'Menace Moyenne',
    threat_low: 'Menace Faible',
    threat_minimal: 'Menace Minimale',
    
    location: 'Localisation',
    getting_location: 'Obtention de la localisation...',
    location_unavailable: 'Localisation indisponible',
    
    just_now: "À l'instant",
    hours_ago: 'il y a {n}h',
    days_ago: 'il y a {n}j',
  },
  
  ar: {
    app_name: 'Good Shepherd',
    loading: 'جاري التحميل...',
    error: 'خطأ',
    success: 'نجاح',
    cancel: 'إلغاء',
    save: 'حفظ',
    close: 'إغلاق',
    retry: 'إعادة المحاولة',
    
    online: 'متصل',
    offline: 'غير متصل',
    offline_notice: 'أنت غير متصل. ستتم مزامنة البيانات عند الاتصال.',
    
    checkin_title: 'تسجيل السلامة',
    checkin_subtitle: 'أخبر فريقك أنك بخير',
    checkin_safe: 'أنا بخير',
    checkin_caution: 'حذر',
    checkin_help: 'أحتاج مساعدة',
    checkin_send: 'إرسال التسجيل',
    checkin_success: 'تم تسجيل الحضور',
    checkin_synced: 'تم إرسال حالتك إلى المنسق.',
    checkin_pending: 'سيتم مزامنة تسجيلك عند الاتصال مجدداً.',
    checkin_last: 'آخر تسجيل',
    checkin_add_note: 'إضافة ملاحظة (اختياري)',
    
    alerts: 'التنبيهات',
    no_alerts: 'لا توجد تنبيهات حرجة في منطقتك',
    unacknowledged: 'تنبيهات غير مؤكدة',
    recent_events: 'أحداث حديثة عالية الأولوية',
    got_it: 'فهمت',
    
    daily_brief: 'الملخص اليومي',
    critical: 'حرج',
    high: 'عالي',
    medium: 'متوسط',
    low: 'منخفض',
    total: 'المجموع',
    monitoring: 'المراقبة',
    
    emergency_contacts: 'جهات اتصال الطوارئ',
    emergency_line: 'خط الطوارئ',
    regional_coordinator: 'المنسق الإقليمي',
    local_embassy: 'السفارة المحلية',
    
    nav_alerts: 'التنبيهات',
    nav_brief: 'الملخص',
    nav_contacts: 'جهات الاتصال',
    nav_settings: 'الإعدادات',
    
    settings: 'الإعدادات',
    language: 'اللغة',
    notifications: 'الإشعارات',
    push_notifications: 'إشعارات الدفع',
    sms_fallback: 'رسائل SMS الاحتياطية',
    region_settings: 'إعدادات المنطقة',
    your_region: 'منطقتك',
    offline_data: 'البيانات غير المتصلة',
    clear_cache: 'مسح ذاكرة التخزين',
    storage_used: 'التخزين المستخدم',
    
    threat_critical: 'تهديد حرج',
    threat_high: 'تهديد عالي',
    threat_medium: 'تهديد متوسط',
    threat_low: 'تهديد منخفض',
    threat_minimal: 'تهديد ضئيل',
    
    location: 'الموقع',
    getting_location: 'جاري الحصول على الموقع...',
    location_unavailable: 'الموقع غير متاح',
    
    just_now: 'الآن',
    hours_ago: 'منذ {n} ساعة',
    days_ago: 'منذ {n} يوم',
  },
};

// Current language state
let currentLanguage = 'en';

/**
 * Initialize i18n with user's preferred language
 */
export function initI18n() {
  // Check localStorage first
  const stored = localStorage.getItem('language');
  if (stored && LANGUAGES[stored]) {
    currentLanguage = stored;
  } else {
    // Try to detect from browser
    const browserLang = navigator.language?.split('-')[0];
    if (browserLang && LANGUAGES[browserLang]) {
      currentLanguage = browserLang;
    }
  }
  
  // Set document direction for RTL languages
  updateDocumentDirection();
  
  return currentLanguage;
}

/**
 * Get current language
 */
export function getLanguage() {
  return currentLanguage;
}

/**
 * Set language
 */
export function setLanguage(lang) {
  if (LANGUAGES[lang]) {
    currentLanguage = lang;
    localStorage.setItem('language', lang);
    updateDocumentDirection();
    return true;
  }
  return false;
}

/**
 * Update document direction for RTL support
 */
function updateDocumentDirection() {
  const langConfig = LANGUAGES[currentLanguage];
  if (langConfig) {
    document.documentElement.dir = langConfig.dir;
    document.documentElement.lang = currentLanguage;
  }
}

/**
 * Translate a key
 */
export function t(key, params = {}) {
  const langStrings = translations[currentLanguage] || translations.en;
  let text = langStrings[key] || translations.en[key] || key;
  
  // Replace parameters
  Object.entries(params).forEach(([param, value]) => {
    text = text.replace(`{${param}}`, value);
  });
  
  return text;
}

/**
 * React hook for translations
 */
export function useTranslation() {
  return {
    t,
    language: currentLanguage,
    setLanguage,
    languages: LANGUAGES,
  };
}

export default {
  initI18n,
  getLanguage,
  setLanguage,
  t,
  useTranslation,
  LANGUAGES,
};
