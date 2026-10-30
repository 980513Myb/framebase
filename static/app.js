const { createApp, reactive, ref, computed, onMounted, watch, onUnmounted, nextTick } = Vue;

createApp({
    setup() {
        const initialHashTab = (window.location.hash || '').replace('#', '');
        const designerRoute = ['custom', 'design'].includes(initialHashTab);
        const creationMode = ref(designerRoute ? 'designer' : 'auto');
        const tab = ref(designerRoute ? 'custom' : (initialHashTab || 'dashboard'));
        const servers = ref([]);
        const fontList = ref([]);
        const layoutList = ref([]); 
        const presetList = ref([]);
        const layoutGroups = ref([]); 
        const orderedLayoutGroups = computed(() => {
            const layoutOrder = new Map(layoutList.value.map((layout, index) => [layout, index]));
            return layoutGroups.value
                .map((group, index) => ({ group, index }))
                .sort((left, right) => {
                    if (left.group.kind !== right.group.kind) return left.group.kind === 'system' ? -1 : 1;
                    if (left.group.kind !== 'system') return left.index - right.index;
                    const leftOrder = layoutOrder.get(left.group.layout) ?? Number.MAX_SAFE_INTEGER;
                    const rightOrder = layoutOrder.get(right.group.layout) ?? Number.MAX_SAFE_INTEGER;
                    return leftOrder - rightOrder || left.index - right.index;
                })
                .map(({ group }) => group);
        });
        const bottomMenu = ref(null);
        const coverTabs = ['manual', 'custom', 'auto', 'library_preview', 'fonts', 'templates', 'translations'];
        const automationTabs = ['webhook'];
        const settingsTabs = ['server', 'library_preview', 'fonts', 'translations', 'account'];
        const validTabs = ['dashboard', 'config_notification', 'logs', ...coverTabs, ...automationTabs, ...settingsTabs];
        const tabAliases = {
            backup: 'library_preview',
            cover_backup: 'library_preview',
            design: 'custom',
            settings: 'server',
            notification: 'config_notification',
            proxy: 'server',
            tmdb: 'server'
        };
        const savedAuthToken = localStorage.getItem('authToken');
        if (savedAuthToken) {
            axios.defaults.headers.common.Authorization = `Bearer ${savedAuthToken}`;
        }
        axios.interceptors.response.use(
            response => response,
            error => {
                if (error.response?.status === 401 && error.response?.data?.detail === '登录已失效，请重新登录') {
                    localStorage.removeItem('isLoggedIn');
                    localStorage.removeItem('authToken');
                    window.location.href = 'login.html';
                }
                return Promise.reject(error);
            }
        );
        const normalizeTab = (raw) => tabAliases[raw] || raw;
        tab.value = normalizeTab(tab.value);
        if (!validTabs.includes(tab.value)) tab.value = 'dashboard';
        const syncTabFromHash = () => {
            const raw = (window.location.hash || '').replace('#', '');
            const next = normalizeTab(raw);
            if (validTabs.includes(next)) {
                if (next === 'custom') creationMode.value = 'designer';
                if (next === 'manual') creationMode.value = 'auto';
                tab.value = next;
                bottomMenu.value = null;
                settingsOpen.value = false;
                creationOpen.value = false;
            }
        };
        const isCoverTab = computed(() => coverTabs.includes(tab.value));
        const isCreationTab = computed(() => ['manual', 'custom', 'templates'].includes(tab.value));
        const isAutomationTab = computed(() => automationTabs.includes(tab.value));
        const isSettingsTab = computed(() => settingsTabs.includes(tab.value));
        const savedUiMode = localStorage.getItem('framebaseUiMode');
        const uiMode = ref(['night', 'light'].includes(savedUiMode) ? savedUiMode : 'night');
        const commandOpen = ref(false);
        const commandQuery = ref('');
        const commandInput = ref(null);
        const settingsOpen = ref(false);
        const creationOpen = ref(false);
        const commandItems = [
            { tab: 'dashboard', label: '系统概览', hint: '查看工作区状态', icon: 'fa-solid fa-grid-2' },
            { tab: 'manual', label: '创建封面', hint: '打开封面工作台', icon: 'fa-solid fa-wand-magic-sparkles' },
            { tab: 'custom', label: '自由设计', hint: '拖拽搭建个性模板', icon: 'fa-solid fa-object-group' },
            { tab: 'auto', label: '自动任务', hint: '管理定时封面更新', icon: 'fa-solid fa-clock-rotate-left' },
            { tab: 'webhook', label: 'Webhook 自动化', hint: '连接 Emby 事件', icon: 'fa-solid fa-bolt' },
            { tab: 'config_notification', label: '企微通知', hint: '配置消息通道', icon: 'fa-solid fa-bell' },
            { tab: 'server', label: 'Emby 连接', hint: '管理媒体服务器', icon: 'fa-solid fa-server' },
        ];
        const filteredCommandItems = computed(() => {
            const query = commandQuery.value.trim().toLowerCase();
            return query ? commandItems.filter(item => `${item.label} ${item.hint}`.toLowerCase().includes(query)) : commandItems;
        });
        const setUiMode = (mode) => {
            uiMode.value = mode;
            localStorage.setItem('framebaseUiMode', mode);
        };
        const runCommand = (targetTab) => {
            selectBottomTab(targetTab);
            commandOpen.value = false;
            commandQuery.value = '';
        };
        const openSetting = (targetTab) => {
            selectBottomTab(targetTab);
            settingsOpen.value = false;
        };
        const openCreation = (targetTab) => {
            selectBottomTab(targetTab);
            creationOpen.value = false;
        };
        const layoutLabel = (engine) => ({
            '聚焦C佬': '聚焦',
            '旋转堆叠': '经典九宫格',
        }[engine] || engine);
        const webhookPresetLabel = computed(() => {
            const preset = presetList.value.find(item => item.filename === webhookConfig.preset);
            return preset?.name || (webhookConfig.preset ? webhookConfig.preset.replace(/\.json$/i, '').replace(/^preset_/, '模板 ') : '-');
        });
        const selectBottomTab = (targetTab) => {
            const next = normalizeTab(targetTab);
            if (next === 'custom') creationMode.value = 'designer';
            if (next === 'manual') creationMode.value = 'auto';
            tab.value = next;
            bottomMenu.value = null;
            settingsOpen.value = false;
            creationOpen.value = false;
        };
        const toggleBottomMenu = (menu) => {
            bottomMenu.value = bottomMenu.value === menu ? null : menu;
        };

        // ==========================================
        // 0. 版本号与当前用户
        // ==========================================
        const projectVersion = ref('FrameBase v1.0.4');
        const currentUsername = ref(localStorage.getItem('username') || 'Administrator'); 

        // ==========================================
        // 1. Toast 通知系统
        // ==========================================
        const toasts = ref([]);
        let toastId = 0;
        
        const showToast = (msg, type = 'success') => {
            const id = toastId++;
            let icon = 'fa-circle-check';
            if (type === 'error') icon = 'fa-circle-xmark';
            if (type === 'info') icon = 'fa-circle-info';
            
            toasts.value.push({ id, msg, type, icon });
            
            setTimeout(() => {
                const idx = toasts.value.findIndex(t => t.id === id);
                if (idx !== -1) toasts.value.splice(idx, 1);
            }, 3000);
        };

        const apiErrorMessage = (e, fallback = '操作失败') => {
            const detail = e?.response?.data?.detail || e?.response?.data?.message || e?.message;
            return detail ? `${fallback}: ${detail}` : fallback;
        };

        // ==========================================
        // 2. Confirm 弹窗系统
        // ==========================================
        const confirmState = reactive({
            visible: false, title: '', msg: '', type: 'warning', icon: 'fa-triangle-exclamation',
            confirmText: '确定', confirmBtnClass: 'btn-primary', resolve: null
        });

        // 选择对话框状态
        const selectState = reactive({
            visible: false, title: '', msg: '', options: [], resolve: null
        });

        const showConfirm = (title, msg, type = 'warning') => {
            return new Promise((resolve) => {
                confirmState.title = title;
                confirmState.msg = msg;
                confirmState.type = type;
                confirmState.visible = true;
                confirmState.resolve = resolve;

                if (type === 'danger') {
                    confirmState.icon = 'fa-trash-can';
                    confirmState.confirmText = '确认删除';
                    confirmState.confirmBtnClass = 'btn-danger';
                } else if (type === 'warning') {
                    confirmState.icon = 'fa-triangle-exclamation';
                    confirmState.confirmText = '确定执行';
                    confirmState.confirmBtnClass = 'btn-primary';
                } else {
                    confirmState.icon = 'fa-circle-info';
                    confirmState.confirmText = '确定';
                    confirmState.confirmBtnClass = 'btn-primary';
                }
            });
        };

        const handleConfirm = (result) => {
            confirmState.visible = false;
            if (confirmState.resolve) { confirmState.resolve(result); confirmState.resolve = null; }
        };

        const showSelectDialog = (title, msg, options) => {
            return new Promise((resolve) => {
                selectState.title = title;
                selectState.msg = msg;
                selectState.options = options;
                selectState.visible = true;
                selectState.resolve = resolve;
            });
        };

        const handleSelect = (index) => {
            selectState.visible = false;
            if (selectState.resolve) { selectState.resolve(index); selectState.resolve = null; }
        };

        const confirmNotificationAction = (channel, action) => {
            return showConfirm(
                '发送测试通知',
                `将通过 ${channel} ${action}。如果配置有效，接收人可能收到测试消息，确定继续吗？`,
                'warning'
            );
        };

        const closeSelectDialog = () => {
            selectState.visible = false;
            if (selectState.resolve) { selectState.resolve(null); selectState.resolve = null; }
        };

        // ==========================================
        // 3. 任务与核心逻辑
        // ==========================================
        
        const tasksState = reactive({
            activeTasks: {}, hasRunning: false, logs: [], logVisible: false, isPolling: false
        });
        
        const consoleLogState = reactive({
            visible: false,
            content: '',
            autoRefresh: true,  // 自动刷新开关
            parsedLogs: [],  // 解析后的日志条目
            loading: false,
            summary: null
        });

        const dashboardStats = reactive({ tasks: 0, auto_tasks: 0, backups: 0, fonts: 0 });
        const dashboardCovers = ref([]);

        const wallRows = reactive([[], [], []]);
        let pollInterval = null;

        const addLog = (type, msg) => {
            const time = new Date().toLocaleTimeString();
            tasksState.logs.unshift({ type, msg, time });
            if (tasksState.logs.length > 50) tasksState.logs.pop();
        };
        
        const clearLogs = async () => {
            const ok = await showConfirm('清空操作记录', '确定清空当前页面里的本地操作记录吗？', 'warning');
            if (!ok) return;
            tasksState.logs.splice(0);
        };

        const stopTask = async (runId) => {
            const ok = await showConfirm('停止任务', '确定要强制停止当前正在运行的任务吗？', 'danger');
            if(!ok) return;
            try {
                await axios.post('/api/stop_task', { run_id: runId });
                showToast("已发送停止请求...", "info");
            } catch {
                showToast("停止失败", "error");
            }
        };

        const processedTaskIds = new Set();
        let isFirstPoll = true;

        const startPolling = () => {
            if (tasksState.isPolling) return;
            tasksState.isPolling = true;

            pollInterval = setInterval(async () => {
                try {
                    const res = await axios.get('/api/progress');
                    const activeMap = res.data;
                    tasksState.activeTasks = activeMap;
                    let running = false;

                    // 首次加载：记录所有已完成任务，不弹通知
                    if (isFirstPoll) {
                        for (const id in activeMap) {
                            const task = activeMap[id];
                            if (task.status === 'finished' || task.status === 'error') {
                                processedTaskIds.add(id);
                            }
                        }
                        isFirstPoll = false;
                        return;
                    }

                    for (const id in activeMap) {
                        const task = activeMap[id];
                        if (task.status === 'running') running = true;

                        if (task.status === 'finished' || task.status === 'error') {
                            if (!processedTaskIds.has(id)) {
                                const msgText = `${task.name} ${task.status === 'finished' ? '完成' : '失败'}`;
                                addLog(task.status === 'finished' ? 'success' : 'error', msgText);

                                if (task.status === 'finished') {
                                    showToast(msgText, 'success');
                                    if (task.name && task.name.startsWith('RSS')) {
                                        console.log("RSS任务完成，自动刷新媒体库...");
                                        refreshAllLibraries();
                                    }
                                    if (task.name && task.name.includes('备份')) fetchSuites();
                                } else {
                                    showToast(msgText, 'error');
                                }

                                processedTaskIds.add(id);

                                setTimeout(() => axios.post('/api/clear_task_progress', { run_id: id }), 3000);
                            }
                        }
                    }
                    
                    for (const cachedId of processedTaskIds) {
                        if (!activeMap[cachedId]) {
                            processedTaskIds.delete(cachedId);
                        }
                    }

                    tasksState.hasRunning = running;
                } catch { }
            }, 1000);
        };

        const stopPolling = () => {
            if (pollInterval) clearInterval(pollInterval);
            tasksState.isPolling = false;
            isFirstPoll = true;
        };

        // 解析日志内容为结构化数据
        const parseLogContent = (content) => {
            if (!content || content.trim() === '') return [];
            const lines = content.split('\n');
            const parsed = [];

            for (const line of lines) {
                if (!line.trim()) continue;

                // 匹配实际日志格式: 2025-02-09 11:42:07 - INFO - message
                const parts = line.split(' - ');
                let timestamp = '';
                let level = 'INFO';
                let message = line.trim();

                if (parts.length >= 3) {
                    // parts[0] = "2025-02-09 11:42:07"
                    // parts[1] = "INFO"
                    // parts[2] = "message"
                    const timeParts = parts[0].trim().split(' ');
                    if (timeParts.length > 1) {
                        timestamp = timeParts[1]; // 只取 HH:MM:SS
                    }
                    level = parts[1].trim().toUpperCase();
                    message = parts.slice(2).join(' - ').trim();

                    // 去掉消息开头的模块标签，如 [System]、[Init] 等
                    message = message.replace(/^\[[\w\s]+\]\s*/, '');
                }

                // 根据级别设置图标和状态
                let icon = 'fa-check';
                let statusClass = 'success';
                let badgeClass = 'info';

                if (level === 'ERROR') {
                    icon = 'fa-times';
                    statusClass = 'error';
                    badgeClass = 'error';
                } else if (level === 'WARNING') {
                    icon = 'fa-exclamation';
                    statusClass = 'warning';
                    badgeClass = 'warning';
                }

                parsed.push({
                    timestamp,
                    level,
                    message,
                    icon,
                    statusClass,
                    badgeClass
                });
            }

            return parsed;
        };

        let consoleLogFetchPending = false;

        const fetchSystemLogs = async (manual = false) => {
            // 如果是自动刷新且自动刷新关闭，直接返回
            if (!manual && !consoleLogState.autoRefresh) return;
            if (consoleLogFetchPending) return;

            const logBody = document.querySelector('.console-log-body');
            const previousScrollTop = logBody ? logBody.scrollTop : 0;
            const wasNearBottom = !logBody || (logBody.scrollHeight - logBody.scrollTop - logBody.clientHeight) < 48;
            const showLoading = manual || !consoleLogState.summary;
            consoleLogFetchPending = true;
            if (showLoading) consoleLogState.loading = true;
            try {
                const res = await axios.get('/api/logs/summary', {
                    params: {
                        limit: logCenterState.limit,
                        category: logCenterState.category,
                        level: logCenterState.level,
                        hours: logCenterState.hours,
                        t: Date.now()
                    }
                });
                consoleLogState.summary = res.data;
                consoleLogState.content = (res.data.entries || []).map(entry => entry.raw || entry.message).join('\n');
                consoleLogState.parsedLogs = (res.data.entries || []).map(entry => ({
                    timestamp: entry.time || '',
                    level: entry.level || 'INFO',
                    message: entry.message || entry.raw || '',
                    icon: entry.level === 'ERROR' ? 'fa-times' : entry.level === 'WARNING' ? 'fa-exclamation' : 'fa-check',
                    statusClass: entry.level === 'ERROR' ? 'error' : entry.level === 'WARNING' ? 'warning' : 'success',
                    badgeClass: (entry.level || 'INFO').toLowerCase(),
                    category: entry.category || 'other',
                    raw: entry.raw || ''
                }));

                nextTick(() => {
                    const el = document.querySelector('.console-log-body');
                    if (el) {
                        el.scrollTop = wasNearBottom ? el.scrollHeight : previousScrollTop;
                    }
                });
            } catch(e) {
                consoleLogState.content = "读取日志失败: " + e.message;
                consoleLogState.parsedLogs = [];
                consoleLogState.summary = null;
            } finally {
                if (showLoading) consoleLogState.loading = false;
                consoleLogFetchPending = false;
            }
        };


        const toggleConsoleAutoScroll = () => {
            consoleLogState.autoRefresh = !consoleLogState.autoRefresh;
            if (consoleLogState.autoRefresh) {
                // 重新启动刷新
                fetchSystemLogs();
            }
        };

        let consoleLogInterval = null;

        const openConsoleLog = () => {
            consoleLogState.visible = true;
            if (consoleLogInterval) clearInterval(consoleLogInterval);
            // 临时修改 #app 的 overflow，允许滚动
            nextTick(() => {
                const app = document.querySelector('#app');
                if (app) app.style.overflow = 'auto';
                // 阻止页面滚动（移动端）
                document.body.style.overflow = 'hidden';
                document.body.style.position = 'fixed';
                document.body.style.width = '100%';
                fetchSystemLogs();
                // 启动自动刷新，每2s获取一次新日志
                consoleLogInterval = setInterval(fetchSystemLogs, 2000);
            });
        };

        const closeConsoleLog = () => {
            consoleLogState.visible = false;
            // 恢复 #app 的 overflow
            const app = document.querySelector('#app');
            if (app) app.style.overflow = 'hidden';
            // 恢复页面滚动（移动端）
            document.body.style.overflow = '';
            document.body.style.position = '';
            document.body.style.width = '';
            // 停止自动刷新
            if (consoleLogInterval) {
                clearInterval(consoleLogInterval);
                consoleLogInterval = null;
            }
        };

        const clearSystemLogs = async () => {
            const ok = await showConfirm('清空后台日志', '确定清空后台日志文件吗？此操作不会影响配置和任务。', 'warning');
            if (!ok) return;
            try {
                const res = await axios.post('/api/clear_system_logs');
                if (res.data.status === 'ok') {
                    consoleLogState.content = '';
                    consoleLogState.parsedLogs = [];
                    consoleLogState.summary = null;
                    logCenterState.summary = null;
                    if (tab.value === 'logs') fetchLogCenter();
                    showToast('日志已清空', 'success');
                }
            } catch(e) {
                console.error('清空日志失败:', e);
                showToast('清空日志失败: ' + (e.response?.data?.detail || e.message), 'error');
            }
        };

        const setConsoleLogCategory = (category) => {
            logCenterState.category = category;
            fetchSystemLogs(true);
        };

        const setConsoleLogLevel = (level) => {
            logCenterState.level = level;
            fetchSystemLogs(true);
        };

        const manualServerIdx = ref(0);
        const currentLibId = ref('');
        const previewImage = ref('');
        const loading = ref(false);
        const applying = ref(false);
        const selectedPresetIdx = ref(''); 
        const currentPresetFile = ref(''); 
        const manualDesignerBaseFile = ref('');
        const manualMode = ref('random');
        
        const accordions = reactive({ 
            materials: true, layout: true, badge: false, target: true, params: false, upload: true
        });
        
        const gradientPresets = {
            aurora: ['#22d3ee', '#6366f1', '#ec4899'],
            sunset: ['#facc15', '#f97316', '#e11d48'],
            mint: ['#d9f99d', '#34d399', '#0891b2'],
            candy: ['#f9a8d4', '#c4b5fd', '#7dd3fc'],
            chrome: ['#ffffff', '#94a3b8', '#f8fafc']
        };
        const applyGradientPreset = (prefix, preset) => {
            const colors = gradientPresets[preset];
            if (!colors) return;
            config[`${prefix}_gradient_start`] = colors[0];
            config[`${prefix}_gradient_middle`] = colors[1];
            config[`${prefix}_gradient_end`] = colors[2];
        };
        const applyDesignerGradientPreset = (element, preset) => {
            const colors = gradientPresets[preset];
            if (!element || !colors) return;
            element.gradientStart = colors[0];
            element.gradientMiddle = colors[1];
            element.gradientEnd = colors[2];
        };
        const config = reactive({ 
            engine: 'classic', badge_style: 'none', badge_font: '', badge_size: 40, badge_bg_color: '#0f172a',
            badge_text_color: '#ffffff', badge_opacity: 255, badge_border_opacity: 40, badge_effect_strength: 70, badge_x_percent: 2, badge_y_percent: 3,
            badge_text_color_mode: 'solid', badge_text_gradient_start: '#ffffff', badge_text_gradient_middle: '#7dd3fc', badge_text_gradient_end: '#f0abfc', badge_text_gradient_direction: 'horizontal',
            badge_bg_color_mode: 'solid', badge_bg_gradient_start: '#22d3ee', badge_bg_gradient_middle: '#6366f1', badge_bg_gradient_end: '#ec4899', badge_bg_gradient_direction: 'diagonal_down',
            title: '', subtitle: '', font_title: '', font_subtitle: '' 
        });
        
        const previewServerIdx = ref(0);
        const libraryCards = ref([]);
        const loadingCovers = ref(false);
        const suiteList = ref([]);
        const newSuiteName = ref('');
        const creatingBackup = ref(false);
        const viewingSuite = ref(null);
        const viewingSuiteImages = ref([]);
        const selectedRestoreIds = ref([]);
        
        const autoSelections = reactive({});
        const taskName = ref('');
        const taskCron = ref('');
        const taskEngine = ref('classic'); 
        const taskPreset = ref('');
        const runningTask = ref(false);
        const taskList = ref([]); 
        const taskMode = ref('random');
        const taskFallbackToNextBackdrop = ref(true);
        const editingTaskId = ref(null);
        const showCreateTask = ref(false);
        const selectedAutoTargetCount = computed(() => {
            return Object.values(autoSelections).reduce((total, list) => total + (Array.isArray(list) ? list.length : 0), 0);
        });

        const translationList = ref([]);
        const transServerIdx = ref(0); 
        const coverAssets = reactive({ bg_url: null, posters: [] });
        const materialModalVisible = ref(false);
        const materialModalType = ref('Backdrop');
        const materialModalSource = ref('pool');
        const materialModalStep = ref('list');
        const materialModalImages = ref([]);
        const materialModalLoading = ref(false);
        const materialSearchQuery = ref('');
        const materialSearchResults = ref([]);

        const defaultDesignerBgColor = (mode = uiMode.value) => mode === 'light' ? '#f4f8fb' : '#101820';
        const designerCanvas = ref(null);
        const designerElements = ref([]);
        const selectedDesignerId = ref('');
        const designerTextEditingId = ref('');
        const designerTextEditingOriginal = ref('');
        const designerLayerDragId = ref('');
        const designerLayerDropId = ref('');
        const designerLayerDropEdge = ref('');
        const designerBgColor = ref(defaultDesignerBgColor());
        const designerBackgroundCustomized = ref(false);
        const designerGrid = ref(true);
        const designerSnap = ref(true);
        const designerStage = ref('edit');
        const designerTemplateName = ref('');
        const selectedDesignerPreset = ref('');
        const currentDesignerPresetFile = ref('');
        const designerHistory = ref([]);
        const designerHistoryIndex = ref(-1);
        const selectedTemplates = ref([]);
        const templatePreviewVersion = ref(Date.now());
        const templateImportInput = ref(null);
        
        const layoutSchemas = ref({});
        const accountForm = reactive({ old_password: '', new_username: '', new_password: '' });
        const updatingAccount = ref(false);

        const bgUploadInput = ref(null);
        const posterUploadInput = ref(null);
        const fontUploadInput = ref(null);

        const fileInputs = {
            background: bgUploadInput,
            poster: posterUploadInput,
            font: fontUploadInput,
            template: templateImportInput
        };

        const triggerFileInput = (type) => {
            const target = fileInputs[type];
            if (target?.value) target.value.click();
        };

        const designerTypeMeta = {
            backdrop: { label: '背景框', icon: 'fa-image' },
            poster: { label: '海报框', icon: 'fa-images' },
            text: { label: '文字', icon: 'fa-font' },
            shape: { label: '装饰框', icon: 'fa-square' }
        };
        const isDesignerVariant = (preset) => Boolean(preset?.config?.designer_parent);
        const isDesignerLayoutPreset = (preset) => preset?.engine === '自由设计'
            && !isDesignerVariant(preset)
            && (preset.config?.designer_role === 'layout' || String(preset.filename || '').startsWith('designer_'));
        const designerPresets = computed(() => presetList.value.filter(item => isDesignerLayoutPreset(item)));
        const selectedDesignerElement = computed(() => designerElements.value.find(item => item.id === selectedDesignerId.value) || null);
        const normalizeDesignerElement = (source = {}) => {
            const element = { ...source };
            const common = {
                x: 0, y: 0, w: 480, h: 320, rotation: 0, opacity: 100, hidden: false
            };
            Object.entries(common).forEach(([key, value]) => {
                if (element[key] === undefined || element[key] === null || element[key] === '') element[key] = value;
            });
            if (['poster', 'backdrop', 'shape'].includes(element.type)) {
                const defaults = { radius: 0, borderWidth: 0, borderColor: '#ffffff', fill: '#22313f' };
                Object.entries(defaults).forEach(([key, value]) => {
                    if (element[key] === undefined || element[key] === null || element[key] === '') element[key] = value;
                });
            }
            if (['poster', 'backdrop'].includes(element.type)) {
                if (!element.fit) element.fit = 'cover';
                if (element.assetIndex === undefined) element.assetIndex = 0;
            }
            if (element.type === 'poster') {
                const ratio = Number(element.aspectRatio);
                element.aspectRatio = Number.isFinite(ratio) && ratio > 0 ? ratio : (2 / 3);
                element.h = Math.round(Number(element.w) / element.aspectRatio);
                element.fit = 'cover';
            }
            if (element.type === 'text') {
                const color = element.color || '#ffffff';
                const textDefaults = {
                    textSource: 'custom', text: '自定义文字', font: '', fontSize: 96,
                    color, colorMode: 'solid', gradientStart: color,
                    gradientMiddle: '#5eead4', gradientEnd: '#60a5fa',
                    gradientDirection: 'horizontal', align: 'left', verticalAlign: 'center',
                    lineHeight: 1.15, strokeWidth: 0, strokeColor: '#000000'
                };
                Object.entries(textDefaults).forEach(([key, value]) => {
                    if (element[key] === undefined || element[key] === null || element[key] === '') element[key] = value;
                });
            }
            return element;
        };
        const normalizeDesignerElements = (elements) => Array.isArray(elements)
            ? elements.map(item => normalizeDesignerElement(item))
            : [];
        const manualDesignerElements = computed(() => Array.isArray(config.designer_elements) ? config.designer_elements : []);
        const manualDesignerBackdropElements = computed(() => manualDesignerElements.value.filter(item => item.type === 'backdrop'));
        const manualDesignerPosterElements = computed(() => manualDesignerElements.value.filter(item => item.type === 'poster'));
        const manualDesignerTextElements = computed(() => manualDesignerElements.value.filter(item => item.type === 'text'));
        const manualDesignerShapeElements = computed(() => manualDesignerElements.value.filter(item => item.type === 'shape'));
        const setManualDesignerGroupValue = (elements, key, value) => {
            (elements || []).forEach(element => { element[key] = value; });
        };
        const designerPosterAspectRatio = (element) => {
            const ratio = Number(element?.aspectRatio);
            return Number.isFinite(ratio) && ratio > 0 ? ratio : (2 / 3);
        };
        const resizeDesignerPoster = (element, width, commit = false) => {
            if (!element || element.type !== 'poster') return;
            const ratio = designerPosterAspectRatio(element);
            const boundedWidth = Math.max(40, Math.min(1440, 2160 * ratio, Number(width) || 40));
            element.w = Math.round(boundedWidth);
            element.h = Math.round(boundedWidth / ratio);
            if (commit) commitDesignerHistory();
        };
        const setManualDesignerPosterSize = (width) => {
            manualDesignerPosterElements.value.forEach(element => resizeDesignerPoster(element, width));
        };
        const manualDesignerElementLabel = (element, index) => {
            if (!element) return `图层 ${index + 1}`;
            if (element.type === 'text') {
                const labels = { title: '主标题', subtitle: '副标题', count: '媒体数量', custom: '自定义文字' };
                return labels[element.textSource] || `文字 ${index + 1}`;
            }
            const typeLabel = designerTypeMeta[element.type]?.label || '图层';
            const sameType = manualDesignerElements.value.slice(0, index + 1).filter(item => item.type === element.type).length;
            return `${typeLabel} ${sameType}`;
        };
        const designerElementLabel = (element) => {
            if (!element) return '';
            if (element.type === 'text') {
                const labels = { title: '主标题', subtitle: '副标题', count: '媒体数量', custom: '自定义文字' };
                return labels[element.textSource] || element.name || '文字';
            }
            const sameType = designerElements.value.filter(item => item.type === element.type);
            return `${designerTypeMeta[element.type]?.label || '图层'} ${sameType.indexOf(element) + 1}`;
        };
        const makeDesignerId = () => `layer_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
        const preferredDesignerFont = () => {
            const preferred = ['OPPOSans-B.ttf', '优设标题黑.ttf', '仓耳舒圆体W02.ttf', 'OPPOSans-M.ttf', 'OPPOSans-R.ttf'];
            return preferred.find(name => fontList.value.includes(name)) || fontList.value.find(name => /[\u3400-\u9fff]/.test(name)) || fontList.value[0] || '';
        };
        const snapDesignerValue = (value, axis = 'x') => {
            const step = axis === 'y' ? 40 : 20;
            return designerSnap.value ? Math.round(value / step) * step : Math.round(value);
        };
        const designerPositionBounds = (element) => {
            if (element.type === 'poster') {
                const visibleEdge = 40;
                return {
                    minX: visibleEdge - Number(element.w),
                    maxX: 1920 - visibleEdge,
                    minY: visibleEdge - Number(element.h),
                    maxY: 1080 - visibleEdge
                };
            }
            return {
                minX: 0,
                maxX: Math.max(0, 1920 - Number(element.w)),
                minY: 0,
                maxY: Math.max(0, 1080 - Number(element.h))
            };
        };
        const moveDesignerElement = (element, x, y) => {
            const bounds = designerPositionBounds(element);
            element.x = Math.max(bounds.minX, Math.min(bounds.maxX, snapDesignerValue(x, 'x')));
            element.y = Math.max(bounds.minY, Math.min(bounds.maxY, snapDesignerValue(y, 'y')));
        };
        const cloneDesignerState = () => JSON.stringify({
            bg: designerBgColor.value,
            bgCustomized: designerBackgroundCustomized.value,
            elements: designerElements.value
        });
        const resetDesignerHistory = () => {
            designerHistory.value = [cloneDesignerState()];
            designerHistoryIndex.value = 0;
        };
        const commitDesignerHistory = () => {
            const snapshot = cloneDesignerState();
            if (designerHistory.value[designerHistoryIndex.value] === snapshot) return;
            designerHistory.value = designerHistory.value.slice(0, designerHistoryIndex.value + 1);
            designerHistory.value.push(snapshot);
            if (designerHistory.value.length > 60) designerHistory.value.shift();
            designerHistoryIndex.value = designerHistory.value.length - 1;
            previewImage.value = '';
            designerStage.value = 'edit';
        };
        const restoreDesignerHistory = (index) => {
            const snapshot = designerHistory.value[index];
            if (!snapshot) return;
            const state = JSON.parse(snapshot);
            designerBgColor.value = state.bg;
            designerBackgroundCustomized.value = state.bgCustomized === true;
            designerElements.value = state.elements;
            designerHistoryIndex.value = index;
            if (!designerElements.value.some(item => item.id === selectedDesignerId.value)) selectedDesignerId.value = '';
            previewImage.value = '';
            designerStage.value = 'edit';
        };
        const undoDesigner = () => {
            if (designerHistoryIndex.value > 0) restoreDesignerHistory(designerHistoryIndex.value - 1);
        };
        const redoDesigner = () => {
            if (designerHistoryIndex.value < designerHistory.value.length - 1) restoreDesignerHistory(designerHistoryIndex.value + 1);
        };
        const addDesignerElement = (type, textSource = 'custom') => {
            const offset = (designerElements.value.length * 28) % 220;
            const common = { id: makeDesignerId(), type, x: 120 + offset, y: 100 + offset, rotation: 0, opacity: 100, hidden: false };
            let element;
            if (type === 'backdrop') {
                element = { ...common, x: 0, y: 0, w: 1920, h: 1080, assetIndex: 0, radius: 0, borderWidth: 0, borderColor: '#ffffff', fill: '#22313f', fit: 'cover' };
            } else if (type === 'poster') {
                const posterIndex = designerElements.value.filter(item => item.type === 'poster').length;
                element = { ...common, w: 380, h: 570, aspectRatio: 2 / 3, assetIndex: posterIndex, radius: 24, borderWidth: 4, borderColor: '#ffffff', fill: '#22313f', fit: 'cover' };
            } else if (type === 'shape') {
                element = { ...common, w: 540, h: 180, radius: 18, borderWidth: 3, borderColor: '#48ccff', fill: '#1479d7' };
            } else {
                const defaults = {
                    title: { text: '媒体库标题', fontSize: 132, w: 920, h: 190 },
                    subtitle: { text: 'Library subtitle', fontSize: 64, w: 920, h: 120 },
                    count: { text: '0', fontSize: 80, w: 260, h: 130 },
                    custom: { text: '自定义文字', fontSize: 84, w: 720, h: 150 }
                }[textSource] || {};
                element = normalizeDesignerElement({ ...common, ...defaults, type: 'text', textSource, font: preferredDesignerFont(), color: '#ffffff', align: 'left', verticalAlign: 'center', lineHeight: 1.15, strokeWidth: 0, strokeColor: '#000000' });
            }
            if (type === 'backdrop') designerElements.value.unshift(element);
            else designerElements.value.push(element);
            selectedDesignerId.value = element.id;
            commitDesignerHistory();
        };
        const removeDesignerElement = (id = selectedDesignerId.value) => {
            const index = designerElements.value.findIndex(item => item.id === id);
            if (index < 0) return;
            if (designerTextEditingId.value === id) designerTextEditingId.value = '';
            designerElements.value.splice(index, 1);
            selectedDesignerId.value = designerElements.value[Math.min(index, designerElements.value.length - 1)]?.id || '';
            commitDesignerHistory();
        };
        const duplicateDesignerElement = () => {
            const source = selectedDesignerElement.value;
            if (!source) return;
            const copy = JSON.parse(JSON.stringify(source));
            copy.id = makeDesignerId();
            moveDesignerElement(copy, copy.x + 40, copy.y + 40);
            if (copy.type === 'poster') copy.assetIndex = designerElements.value.filter(item => item.type === 'poster').length;
            designerElements.value.push(copy);
            selectedDesignerId.value = copy.id;
            commitDesignerHistory();
        };
        const moveDesignerLayer = (direction) => {
            const index = designerElements.value.findIndex(item => item.id === selectedDesignerId.value);
            const target = index + direction;
            if (index < 0 || target < 0 || target >= designerElements.value.length) return;
            [designerElements.value[index], designerElements.value[target]] = [designerElements.value[target], designerElements.value[index]];
            commitDesignerHistory();
        };
        const startDesignerLayerReorder = (event, element) => {
            if (event.button !== undefined && event.button !== 0) return;
            event.preventDefault();
            selectedDesignerId.value = element.id;
            designerLayerDragId.value = element.id;
            designerLayerDropId.value = '';
            designerLayerDropEdge.value = '';

            const onMove = (moveEvent) => {
                moveEvent.preventDefault();
                const row = document.elementFromPoint(moveEvent.clientX, moveEvent.clientY)?.closest('[data-designer-layer-id]');
                const targetId = row?.dataset.designerLayerId || '';
                if (!targetId || targetId === designerLayerDragId.value) {
                    designerLayerDropId.value = '';
                    designerLayerDropEdge.value = '';
                    return;
                }
                const rect = row.getBoundingClientRect();
                designerLayerDropId.value = targetId;
                designerLayerDropEdge.value = moveEvent.clientY < rect.top + rect.height / 2 ? 'above' : 'below';
            };
            const onUp = () => {
                window.removeEventListener('pointermove', onMove);
                window.removeEventListener('pointerup', onUp);
                const sourceId = designerLayerDragId.value;
                const targetId = designerLayerDropId.value;
                const edge = designerLayerDropEdge.value;
                designerLayerDragId.value = '';
                designerLayerDropId.value = '';
                designerLayerDropEdge.value = '';
                if (!sourceId || !targetId || sourceId === targetId) return;
                const sourceIndex = designerElements.value.findIndex(item => item.id === sourceId);
                if (sourceIndex < 0) return;
                const [moved] = designerElements.value.splice(sourceIndex, 1);
                let targetIndex = designerElements.value.findIndex(item => item.id === targetId);
                if (targetIndex < 0) {
                    designerElements.value.splice(sourceIndex, 0, moved);
                    return;
                }
                if (edge === 'above') targetIndex += 1;
                designerElements.value.splice(targetIndex, 0, moved);
                commitDesignerHistory();
            };
            window.addEventListener('pointermove', onMove, { passive: false });
            window.addEventListener('pointerup', onUp, { once: true });
        };
        const toggleDesignerLayer = (element) => {
            element.hidden = !element.hidden;
            commitDesignerHistory();
        };
        const designerElementStyle = (element, index) => ({
            left: `${element.x / 19.2}%`,
            top: `${element.y / 10.8}%`,
            width: `${element.w / 19.2}%`,
            height: `${element.h / 10.8}%`,
            zIndex: index + 1,
            opacity: element.opacity / 100,
            transform: `rotate(${element.rotation || 0}deg)`,
            borderRadius: `${Math.min(50, (element.radius || 0) / Math.max(1, Math.min(element.w, element.h)) * 100)}%`,
            backgroundColor: element.type === 'shape' ? element.fill : undefined,
            borderWidth: `${Math.max(0, (element.borderWidth || 0) / 5)}px`,
            borderColor: element.borderColor || 'transparent',
            color: element.color || '#ffffff',
            fontFamily: element.font ? `'${element.font}', 'OPPOSans-B.ttf', 'OPPOSans-R.ttf', sans-serif` : `'OPPOSans-B.ttf', 'OPPOSans-R.ttf', sans-serif`,
            fontSize: element.type === 'text' ? `${element.fontSize / 10.8}cqh` : undefined,
            textAlign: element.align || 'left',
            alignItems: element.verticalAlign === 'top' ? 'flex-start' : (element.verticalAlign === 'bottom' ? 'flex-end' : 'center')
        });
        const designerTextPaintStyle = (element) => {
            if (element?.colorMode !== 'gradient') return { color: element?.color || '#ffffff' };
            const directions = {
                horizontal: '90deg', vertical: '180deg', diagonal_down: '135deg', diagonal_up: '45deg'
            };
            return {
                color: 'transparent',
                backgroundImage: `linear-gradient(${directions[element.gradientDirection] || '90deg'}, ${element.gradientStart}, ${element.gradientMiddle}, ${element.gradientEnd})`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text'
            };
        };
        const designerTextPreview = (element) => {
            if (element.textSource === 'title') return currentLibId.value ? (config.title || '媒体库标题') : '媒体库标题';
            if (element.textSource === 'subtitle') return currentLibId.value ? (config.subtitle || '媒体库副标题') : '媒体库副标题';
            if (element.textSource === 'count') return '128';
            return element.text || '自定义文字';
        };
        const startDesignerTextEdit = (event, element) => {
            if (element?.type !== 'text' || element.textSource !== 'custom') return;
            event.preventDefault();
            event.stopPropagation();
            selectedDesignerId.value = element.id;
            designerTextEditingId.value = element.id;
            designerTextEditingOriginal.value = element.text || '';
            nextTick(() => {
                const editor = designerCanvas.value?.querySelector(`[data-inline-text-editor="${element.id}"]`);
                editor?.focus();
                editor?.select();
            });
        };
        const finishDesignerTextEdit = (element, cancel = false) => {
            if (!element || designerTextEditingId.value !== element.id) return;
            if (cancel) element.text = designerTextEditingOriginal.value;
            designerTextEditingId.value = '';
            designerTextEditingOriginal.value = '';
            commitDesignerHistory();
        };
        const startDesignerPointer = (event, element, action = 'move') => {
            if (!designerCanvas.value || element.hidden || designerTextEditingId.value === element.id) return;
            event.preventDefault();
            selectedDesignerId.value = element.id;
            const rect = designerCanvas.value.getBoundingClientRect();
            const startX = event.clientX;
            const startY = event.clientY;
            const original = { x: Number(element.x), y: Number(element.y), w: Number(element.w), h: Number(element.h), rotation: Number(element.rotation || 0) };
            const center = {
                x: rect.left + (original.x + original.w / 2) / 1920 * rect.width,
                y: rect.top + (original.y + original.h / 2) / 1080 * rect.height
            };
            const startAngle = Math.atan2(startY - center.y, startX - center.x) * 180 / Math.PI;
            const onMove = (moveEvent) => {
                const dx = (moveEvent.clientX - startX) / rect.width * 1920;
                const dy = (moveEvent.clientY - startY) / rect.height * 1080;
                if (action === 'resize') {
                    if (element.type === 'poster') {
                        const scaleDelta = (dx * original.w + dy * original.h) / Math.max(1, original.w ** 2 + original.h ** 2);
                        const ratio = designerPosterAspectRatio(element);
                        const maxWidth = Math.min(1440, 2160 * ratio);
                        const width = Math.max(40, Math.min(maxWidth, original.w * (1 + scaleDelta)));
                        resizeDesignerPoster(element, designerSnap.value ? Math.round(width / 20) * 20 : Math.round(width));
                    } else {
                        const maxWidth = Math.max(40, 1920 - original.x);
                        const maxHeight = Math.max(40, 1080 - original.y);
                        element.w = Math.max(40, Math.min(maxWidth, snapDesignerValue(original.w + dx, 'x')));
                        element.h = Math.max(40, Math.min(maxHeight, snapDesignerValue(original.h + dy, 'y')));
                    }
                } else if (action === 'rotate') {
                    const angle = Math.atan2(moveEvent.clientY - center.y, moveEvent.clientX - center.x) * 180 / Math.PI;
                    const rotation = original.rotation + angle - startAngle;
                    element.rotation = designerSnap.value ? Math.round(rotation / 5) * 5 : Math.round(rotation);
                } else {
                    moveDesignerElement(element, original.x + dx, original.y + dy);
                }
            };
            const onUp = () => {
                window.removeEventListener('pointermove', onMove);
                window.removeEventListener('pointerup', onUp);
                commitDesignerHistory();
            };
            window.addEventListener('pointermove', onMove, { passive: false });
            window.addEventListener('pointerup', onUp, { once: true });
        };
        const newDesignerTemplate = () => {
            designerTextEditingId.value = '';
            designerElements.value = [];
            designerBgColor.value = defaultDesignerBgColor();
            designerBackgroundCustomized.value = false;
            selectedDesignerId.value = '';
            selectedDesignerPreset.value = '';
            currentDesignerPresetFile.value = '';
            designerTemplateName.value = '';
            previewImage.value = '';
            designerStage.value = 'edit';
            resetDesignerHistory();
        };
        const buildDesignerConfig = (includeLibraryContent = true) => {
            const posterElements = designerElements.value.filter(item => item.type === 'poster');
            return {
                engine: '自由设计',
                badge_style: 'none',
                title: includeLibraryContent ? config.title : '',
                subtitle: includeLibraryContent ? config.subtitle : '',
                designer_role: 'layout',
                canvas_bg_color: designerBgColor.value,
                designer_elements: JSON.parse(JSON.stringify(designerElements.value)),
                poster_count: Math.max(1, ...posterElements.map(item => Number(item.assetIndex || 0) + 1)),
                backdrop_count: designerElements.value.some(item => item.type === 'backdrop') ? 1 : 0
            };
        };
        const loadDesignerPreset = () => {
            const preset = designerPresets.value.find(item => item.filename === selectedDesignerPreset.value);
            if (!preset) return;
            designerTextEditingId.value = '';
            designerBgColor.value = preset.config.canvas_bg_color || defaultDesignerBgColor();
            designerBackgroundCustomized.value = true;
            designerElements.value = normalizeDesignerElements(JSON.parse(JSON.stringify(preset.config.designer_elements || []))).map(item => ({ ...item, id: item.id || makeDesignerId(), hidden: item.hidden === true }));
            designerTemplateName.value = preset.name;
            currentDesignerPresetFile.value = preset.filename;
            selectedDesignerId.value = designerElements.value.at(-1)?.id || '';
            previewImage.value = '';
            designerStage.value = 'edit';
            resetDesignerHistory();
            showToast(`已加载模板: ${preset.name}`, 'success');
        };
        const updateDesignerBackground = () => {
            designerBackgroundCustomized.value = true;
            commitDesignerHistory();
        };
        const saveDesignerTemplate = async (overwrite = false) => {
            const name = designerTemplateName.value.trim();
            if (!name) return showToast('请填写模板名称', 'error');
            const filename = overwrite && currentDesignerPresetFile.value ? currentDesignerPresetFile.value : `designer_${Date.now()}.json`;
            try {
                let imageData = previewImage.value || null;
                if (!imageData && currentLibId.value) {
                    const rendered = await axios.post('/api/preview', getCoverPayload());
                    imageData = rendered.data.image;
                    previewImage.value = imageData;
                }
                await axios.post('/api/save_template', { filename, name, engine: '自由设计', config: buildDesignerConfig(false), image_data: imageData });
                currentDesignerPresetFile.value = filename;
                selectedDesignerPreset.value = filename;
                await fetchLayoutAndPresets();
                showToast(overwrite ? '自由设计模板已更新' : '自由设计模板已保存', 'success');
            } catch (e) {
                showToast(apiErrorMessage(e, '模板保存失败'), 'error');
            }
        };
        const downloadBlob = (blob, filename) => {
            const url = URL.createObjectURL(blob);
            const anchor = document.createElement('a');
            anchor.href = url;
            anchor.download = filename;
            document.body.appendChild(anchor);
            anchor.click();
            anchor.remove();
            window.setTimeout(() => URL.revokeObjectURL(url), 1000);
        };
        const exportTemplate = async (filename) => {
            try {
                const res = await axios.get(`/api/export_template/${encodeURIComponent(filename)}`, { responseType: 'blob' });
                downloadBlob(res.data, filename);
            } catch (e) {
                showToast(apiErrorMessage(e, '模板导出失败'), 'error');
            }
        };
        const toggleTemplateSelection = (filename) => {
            const index = selectedTemplates.value.indexOf(filename);
            if (index >= 0) selectedTemplates.value.splice(index, 1);
            else selectedTemplates.value.push(filename);
        };
        const exportTemplateBatch = async (all = false) => {
            const filenames = all ? presetList.value.map(item => item.filename) : selectedTemplates.value;
            if (!filenames.length) return showToast('请先勾选需要导出的模板', 'error');
            try {
                const res = await axios.post('/api/export_templates', { filenames }, { responseType: 'blob' });
                downloadBlob(res.data, `framebase-templates-${Date.now()}.zip`);
                showToast(`已导出 ${filenames.length} 个模板`, 'success');
            } catch (e) {
                showToast(apiErrorMessage(e, '批量导出失败'), 'error');
            }
        };
        const importTemplates = async (event) => {
            const files = Array.from(event.target.files || []);
            if (!files.length) return;
            let imported = 0;
            for (const file of files) {
                const form = new FormData();
                form.append('file', file);
                try {
                    const res = await axios.post('/api/upload_template', form);
                    imported += (res.data.filenames || []).length;
                } catch (e) {
                    showToast(apiErrorMessage(e, `${file.name} 导入失败`), 'error');
                }
            }
            event.target.value = '';
            await fetchLayoutAndPresets();
            if (imported) showToast(`成功导入 ${imported} 个模板`, 'success');
        };

        const materialModalTitle = computed(() => {
            const source = materialModalSource.value === 'pool' ? '随机池' : '搜索素材';
            const type = materialModalType.value === 'Backdrop' ? '背景图' : '海报';
            return `${source} · ${type}`;
        });
        const clearCoverAssets = (notify = true) => {
            coverAssets.bg_url = null;
            coverAssets.posters.splice(0);
            previewImage.value = '';
            if (notify) showToast('本次指定素材已清空', 'success');
        };
        const handleBgUpload = (event) => {
            const file = event.target.files?.[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (result) => {
                coverAssets.bg_url = result.target.result;
                previewImage.value = '';
            };
            reader.readAsDataURL(file);
            event.target.value = '';
        };
        const handlePosterUpload = (event) => {
            for (const file of Array.from(event.target.files || [])) {
                const reader = new FileReader();
                reader.onload = (result) => {
                    coverAssets.posters.push(result.target.result);
                    previewImage.value = '';
                };
                reader.readAsDataURL(file);
            }
            event.target.value = '';
        };
        const openMaterialPicker = async (type, source) => {
            if (!currentLibId.value) return showToast('请先选择目标媒体库', 'error');
            materialModalVisible.value = true;
            materialModalType.value = type;
            materialModalSource.value = source;
            materialModalImages.value = [];
            materialSearchResults.value = [];
            materialSearchQuery.value = '';
            materialModalStep.value = source === 'search' ? 'list' : 'grid';
            if (source === 'pool') {
                materialModalLoading.value = true;
                try {
                    const server = currentManualServer.value;
                    const res = await axios.post('/api/emby/random_pool', { ...embyConnectionPayload(server), library_id: currentLibId.value, type, limit: 60 });
                    materialModalImages.value = res.data.images || [];
                } catch (e) {
                    showToast(apiErrorMessage(e, '素材池读取失败'), 'error');
                } finally {
                    materialModalLoading.value = false;
                }
            }
        };
        const searchMaterial = async () => {
            if (!materialSearchQuery.value.trim()) return;
            materialModalLoading.value = true;
            materialSearchResults.value = [];
            materialModalStep.value = 'list';
            try {
                const server = currentManualServer.value;
                const res = await axios.post('/api/emby/search', { ...embyConnectionPayload(server), query: materialSearchQuery.value.trim(), library_id: currentLibId.value, type: materialModalType.value });
                materialSearchResults.value = res.data.items || [];
            } catch (e) {
                showToast(apiErrorMessage(e, '素材搜索失败'), 'error');
            } finally {
                materialModalLoading.value = false;
            }
        };
        const fetchMaterialImages = async (itemId) => {
            materialModalLoading.value = true;
            try {
                const server = currentManualServer.value;
                const res = await axios.post('/api/emby/get_images', { ...embyConnectionPayload(server), item_id: itemId, type: materialModalType.value });
                materialModalImages.value = res.data.images || [];
                materialModalStep.value = 'grid';
            } catch (e) {
                showToast(apiErrorMessage(e, '图片读取失败'), 'error');
            } finally {
                materialModalLoading.value = false;
            }
        };
        const toggleMaterialUrl = (url) => {
            if (!url) return;
            const highResUrl = url.replace(/&maxHeight=\d+/, '&maxHeight=2160').replace(/&maxWidth=\d+/, '');
            if (materialModalType.value === 'Backdrop') {
                coverAssets.bg_url = coverAssets.bg_url === highResUrl ? null : highResUrl;
            } else {
                const index = coverAssets.posters.indexOf(highResUrl);
                if (index >= 0) coverAssets.posters.splice(index, 1);
                else coverAssets.posters.push(highResUrl);
            }
            previewImage.value = '';
        };
        const isMaterialSelected = (url) => {
            if (!url) return false;
            const cleanUrl = url.split('&maxHeight')[0];
            return materialModalType.value === 'Backdrop'
                ? Boolean(coverAssets.bg_url && coverAssets.bg_url.includes(cleanUrl))
                : coverAssets.posters.some(item => item.includes(cleanUrl));
        };
        const closeMaterialModal = () => { materialModalVisible.value = false; };

        // ==========================================
        // 4. RSS 相关逻辑 (修改版 - 含编辑功能)
        // ==========================================
        const rssForm = reactive({
            name: '',
            source_type: 'rss',
            cron: '',
            rss_url: '',
            jav_flaresolverr_url: '',
            tmdb_list_type: 'movie_popular',
            target_server_idx: 0,
            content_type: 'movies',
            source_root: '',
            link_root: ''
        });
        const rssTasks = ref([]);
        const tmdbRankingOptions = [
            { value: 'movie_popular', label: '电影热门', content_type: 'movies', media: '电影' },
            { value: 'movie_top_rated', label: '电影高分', content_type: 'movies', media: '电影' },
            { value: 'movie_now_playing', label: '电影热映', content_type: 'movies', media: '电影' },
            { value: 'tv_popular', label: '剧集热门', content_type: 'tvshows', media: '剧集' },
            { value: 'tv_top_rated', label: '剧集高分', content_type: 'tvshows', media: '剧集' },
            { value: 'tv_on_the_air', label: '本周播出', content_type: 'tvshows', media: '剧集' },
            { value: 'trending_movie_week', label: '趋势周榜电影', content_type: 'movies', media: '电影' },
            { value: 'trending_tv_week', label: '趋势周榜电视剧', content_type: 'tvshows', media: '剧集' }
        ];
        const getTmdbRankingOption = (value) => tmdbRankingOptions.find(option => option.value === value) || tmdbRankingOptions[0];
        const tmdbSelectedOption = computed(() => getTmdbRankingOption(rssForm.tmdb_list_type));
        const tmdbListLabel = (value) => getTmdbRankingOption(value).label;
        const tmdbListMedia = (value) => getTmdbRankingOption(value).media;
        const rssTaskSourceLabel = (task) => {
            if (task.source_type === 'javdb') return 'JavDB 榜单';
            if (task.source_type === 'tmdb') return `TMDB · ${tmdbListLabel(task.tmdb_list_type)}`;
            return task.rss_url || '普通 RSS / 豆瓣订阅';
        };
        const rssTaskTypeLabel = (task) => {
            if (task.source_type === 'javdb') return 'JAV 榜单';
            if (task.source_type === 'tmdb') return tmdbListMedia(task.tmdb_list_type);
            return task.content_type === 'tvshows' ? '剧集' : '电影';
        };
        const rssTaskTypeClass = (task) => {
            if (task.source_type === 'javdb') return 'adult';
            return task.content_type === 'tvshows' ? 'tvshows' : 'movies';
        };
        const rssTaskTypeIcon = (task) => {
            if (task.source_type === 'javdb') return 'fa-ranking-star';
            return task.content_type === 'tvshows' ? 'fa-tv' : 'fa-film';
        };
        
        // ★ 新增：记录当前正在编辑的任务ID
        const editingRssTaskId = ref(null); 

        const fetchRssData = async () => {
            try {
                const tRes = await axios.get('/api/rss/tasks');
                rssTasks.value = tRes.data;
            } catch {}
        };

        // 替换原有的 editRssTask
        const editRssTask = (task) => {
            editingRssTaskId.value = task.id;
            // 回填表单数据
            rssForm.name = task.name;
            rssForm.source_type = task.source_type || 'rss';
            rssForm.cron = task.cron;
            rssForm.rss_url = task.rss_url;
            rssForm.jav_flaresolverr_url = task.jav_flaresolverr_url || '';
            rssForm.tmdb_list_type = task.tmdb_list_type || 'movie_popular';
            rssForm.target_server_idx = task.target_server_idx || 0;
            rssForm.content_type = task.content_type || 'movies';
            if (rssForm.source_type === 'tmdb') {
                rssForm.content_type = tmdbSelectedOption.value.content_type;
            }
            rssForm.source_root = task.source_root || '';
            rssForm.link_root = task.link_root || '';
            
            showCreateRss.value = true; // <--- 自动展开表单

            // 滚动到顶部
            const container = document.querySelector('.content-area');
            if (container) container.scrollTop = 0;
        };

        // ★ 新增：取消编辑状态
       // 替换原有的 cancelRssEdit
        const cancelRssEdit = () => {
            editingRssTaskId.value = null;
            rssForm.name = '';
            rssForm.source_type = 'rss';
            rssForm.rss_url = '';
            rssForm.jav_flaresolverr_url = '';
            rssForm.tmdb_list_type = 'movie_popular';
            rssForm.cron = '';
            rssForm.content_type = 'movies';
            rssForm.target_server_idx = 0;
            rssForm.source_root = '';
            rssForm.link_root = '';
            
            showCreateRss.value = false; // <--- 取消时收起表单
        };

        watch(() => rssForm.source_type, (value) => {
            if (value === 'tmdb') {
                rssForm.content_type = tmdbSelectedOption.value.content_type;
                rssForm.rss_url = '';
                rssForm.jav_flaresolverr_url = '';
            } else if (value === 'javdb') {
                rssForm.content_type = 'movies';
                rssForm.rss_url = '';
                rssForm.tmdb_list_type = 'movie_popular';
            } else {
                rssForm.tmdb_list_type = 'movie_popular';
                rssForm.jav_flaresolverr_url = '';
            }
        });

        watch(() => rssForm.tmdb_list_type, () => {
            if (rssForm.source_type === 'tmdb') {
                rssForm.content_type = tmdbSelectedOption.value.content_type;
            }
        });

        const normalizedRssPayload = () => {
            const payload = { ...rssForm };
            if (payload.source_type === 'tmdb') {
                const option = getTmdbRankingOption(payload.tmdb_list_type);
                payload.content_type = option.content_type;
                payload.rss_url = '';
                payload.jav_flaresolverr_url = '';
            } else if (payload.source_type === 'javdb') {
                payload.rss_url = '';
                payload.tmdb_list_type = '';
                payload.content_type = 'movies';
            } else {
                payload.tmdb_list_type = '';
                payload.jav_flaresolverr_url = '';
            }
            return payload;
        };

        // 替换原有的 createRssTask
        const createRssTask = async () => {
            if(!rssForm.name) return showToast('请填写订阅名称', 'error');
            if(!rssForm.cron) return showToast('请填写 Cron 表达式', 'error');
            if(rssForm.source_type === 'rss' && !rssForm.rss_url) return showToast('请填写 RSS URL', 'error');
            if(rssForm.source_type === 'javdb' && !rssForm.jav_flaresolverr_url) return showToast('请填写 Flaresolverr 地址', 'error');
            if(rssForm.source_type === 'tmdb' && !rssForm.tmdb_list_type) return showToast('请选择 TMDB 榜单', 'error');
            if(!rssForm.source_root) return showToast('请填写原始资源目录', 'error');
            if(!rssForm.link_root) return showToast('请填写真实库输出目录', 'error');
            try {
                if (editingRssTaskId.value) {
                    // === 更新模式 ===
                    const originalTask = rssTasks.value.find(t => t.id === editingRssTaskId.value);
                    const enabledState = originalTask ? (originalTask.enabled !== false) : true;
                    
                    const payload = { ...normalizedRssPayload(), id: editingRssTaskId.value, enabled: enabledState };
                    await axios.post('/api/rss/update_task', payload);
                    showToast('RSS 订阅更新成功', 'success');
                    cancelRssEdit(); 
                } else {
                    // === 创建模式 ===
                    const payload = normalizedRssPayload();
                    await axios.post('/api/rss/create_task', payload);
                    showToast('RSS 订阅创建成功', 'success');
                    // 创建成功后清空表单并收起
                    rssForm.name = ''; 
                    rssForm.source_type = 'rss';
                    rssForm.rss_url = '';
                    rssForm.jav_flaresolverr_url = '';
                    rssForm.tmdb_list_type = 'movie_popular';
                    rssForm.cron = '';
                    rssForm.content_type = 'movies';
                    rssForm.source_root = '';
                    rssForm.link_root = '';
                    showCreateRss.value = false; // <--- 创建成功后收起
                }
                fetchRssData();
            } catch (e) { 
                showToast('操作失败: ' + (e.response?.data?.detail || e.message), 'error'); 
            }
        };

        const runRssTask = async (id) => {
            try {
                await axios.post('/api/rss/run_now', { id });
                showToast('RSS 抓取任务已后台运行', 'info');
            } catch { showToast('触发失败', 'error'); }
        };

        const deleteRssTask = async (id) => {
            const confirmTask = await showConfirm('删除订阅', '确定要删除此 RSS 订阅吗？', 'danger');
            if(!confirmTask) return;

            const deleteFiles = await showConfirm(
                '清理关联文件', 
                '是否同时删除硬盘上的硬链接文件和 Emby 中的媒体库？\n\n点击【确定】：彻底删除 (任务+文件+库)\n点击【取消】：仅删除任务配置 (保留文件)', 
                'warning'
            );
            
            try {
                await axios.post('/api/rss/delete_task', { id, delete_files: deleteFiles });
                if (deleteFiles) {
                    showToast('任务及关联资源已彻底删除', 'success');
                } else {
                    showToast('仅删除了任务配置 (文件已保留)', 'success');
                }
                fetchRssData();
            } catch (e) { 
                showToast('删除失败: ' + (e.response?.data?.detail || e.message), 'error'); 
            }
        };

        watch(tab, (val, previous) => {
            if (val === 'custom') creationMode.value = 'designer';
            if (val === 'manual') creationMode.value = 'auto';
            if (val !== previous && ['manual', 'custom'].includes(val)) {
                previewImage.value = '';
                designerStage.value = 'edit';
            }
            if (val !== 'dashboard') bottomMenu.value = null;
            loadTabData(val);
        });

        // ==========================================
        // 5. Webhook 逻辑
        // ==========================================
        const webhookConfig = reactive({
            coverEnabled: false,
            engine: 'classic',
            preset: '',
            mode: 'random'
        });
        const webhookUrl = ref(window.location.origin + '/api/webhook');
        const webhookDebugState = reactive({
            loading: false,
            summary: null,
            payloadText: '',
            parsing: false,
            parseResult: null,
            payloadVisible: false
        });

        const fetchWebhookConfig = async () => {
            try {
                const res = await axios.get('/api/webhook/config');
                Object.assign(webhookConfig, {
                    coverEnabled: Boolean(res.data?.enabled),
                    engine: res.data?.engine || 'classic',
                    preset: res.data?.preset || '',
                    mode: res.data?.mode || 'random'
                });
                validateSelections();
            } catch(e) {}
        };

        const webhookConfigPayload = () => ({
            enabled: Boolean(webhookConfig.coverEnabled),
            engine: webhookConfig.engine || 'classic',
            preset: webhookConfig.preset || '',
            mode: webhookConfig.mode || 'random'
        });

        const saveWebhookConfig = async () => {
            try {
                await axios.post('/api/webhook/config', webhookConfigPayload());
                await fetchWebhookConfig();
                await fetchWebhookDebug();
                showToast('Webhook 配置已保存', 'success');
            } catch(e) {
                showToast('保存失败', 'error');
            }
        };

        const toggleWebhookCoverStatus = async (event) => {
            const newState = event.target.checked;
            const oldState = webhookConfig.coverEnabled;
            webhookConfig.coverEnabled = newState;
            try {
                await axios.post('/api/webhook/config', webhookConfigPayload());
                await fetchWebhookConfig();
                await fetchWebhookDebug();
                showToast(newState ? '入库自动封面已开启' : '入库自动封面已关闭', newState ? 'success' : 'info');
            } catch(e) {
                webhookConfig.coverEnabled = oldState;
                event.target.checked = oldState;
                showToast('状态切换失败', 'error');
            }
        };

        const copyWebhookUrl = () => {
            navigator.clipboard.writeText(webhookUrl.value).then(() => {
                showToast('地址已复制', 'success');
            }).catch(() => {
                showToast('复制失败，请手动复制', 'error');
            });
        };

        const fetchWebhookDebug = async () => {
            webhookDebugState.loading = true;
            try {
                const res = await axios.get('/api/webhook/debug/summary');
                webhookDebugState.summary = res.data;
                if (!webhookDebugState.payloadText && res.data?.payload_example) {
                    webhookDebugState.payloadText = JSON.stringify(res.data.payload_example, null, 2);
                }
            } catch (e) {
                showToast(apiErrorMessage(e, 'Webhook 调试信息读取失败'), 'error');
            } finally {
                webhookDebugState.loading = false;
            }
        };

        const fillWebhookPayloadExample = () => {
            if (!webhookDebugState.summary?.payload_example) return;
            webhookDebugState.payloadText = JSON.stringify(webhookDebugState.summary.payload_example, null, 2);
            webhookDebugState.parseResult = null;
        };

        const parseWebhookPayload = async () => {
            webhookDebugState.parsing = true;
            try {
                const res = await axios.post('/api/webhook/debug/parse', {
                    payload_text: webhookDebugState.payloadText || ''
                });
                webhookDebugState.parseResult = res.data;
                if (!res.data.ok) {
                    showToast(res.data.error || 'Payload 解析失败', 'error');
                }
            } catch (e) {
                webhookDebugState.parseResult = {
                    ok: false,
                    error: e?.response?.data?.detail || e.message || 'Payload 解析失败',
                    preview: {'Event': '', 'Library Name': '', 'Item Name': ''}
                };
                showToast(apiErrorMessage(e, 'Payload 解析失败'), 'error');
            } finally {
                webhookDebugState.parsing = false;
            }
        };

        // ==========================================
        // 5.0 工具系统总览
        // ==========================================
        const toolsState = reactive({
            loading: false,
            summary: null
        });

        const fetchToolsSummary = async () => {
            toolsState.loading = true;
            try {
                const res = await axios.get('/api/tools/summary');
                toolsState.summary = res.data;
            } catch (e) {
                showToast(apiErrorMessage(e, '工具系统状态读取失败'), 'error');
            } finally {
                toolsState.loading = false;
            }
        };

        const toolStatusMeta = (status) => {
            const map = {
                ok: { label: '正常', icon: 'fa-circle-check' },
                warning: { label: '建议检查', icon: 'fa-triangle-exclamation' },
                info: { label: '可选功能', icon: 'fa-circle-info' }
            };
            return map[status] || map.info;
        };

        const openToolCard = (targetTab) => {
            if (!targetTab) return;
            tab.value = targetTab;
            bottomMenu.value = null;
        };

        // ==========================================
        // 5.1 诊断助手
        // ==========================================
        const diagnosticsState = reactive({
            loading: false,
            checking: false,
            summary: null,
            selectedServerIdx: 0,
            embyResult: null
        });

        const fetchDiagnosticsSummary = async () => {
            diagnosticsState.loading = true;
            try {
                const res = await axios.get('/api/diagnostics/summary');
                diagnosticsState.summary = res.data;
                if (diagnosticsState.selectedServerIdx >= (res.data.servers || []).length) {
                    diagnosticsState.selectedServerIdx = 0;
                }
            } catch (e) {
                showToast(apiErrorMessage(e, '诊断信息读取失败'), 'error');
            } finally {
                diagnosticsState.loading = false;
            }
        };

        const runReadonlyEmbyCheck = async () => {
            const server = servers.value[diagnosticsState.selectedServerIdx];
            if (!server || !server.host || !server.key) {
                showToast('请先在 Emby 配置里填写服务器地址和 API Key', 'error');
                return;
            }
            diagnosticsState.checking = true;
            diagnosticsState.embyResult = null;
            try {
                const res = await axios.post('/api/diagnostics/emby_readonly', {
                    host: server.host,
                    key: server.key,
                    public_host: server.public_host || '',
                    user_name: server.user_name || ''
                });
                diagnosticsState.embyResult = res.data;
                showToast(res.data.ok ? '只读检查通过' : '只读检查未通过', res.data.ok ? 'success' : 'error');
            } catch (e) {
                diagnosticsState.embyResult = {
                    ok: false,
                    message: e?.response?.data?.detail || e.message || '只读检查失败',
                    libraries: []
                };
                showToast(apiErrorMessage(e, '只读检查失败'), 'error');
            } finally {
                diagnosticsState.checking = false;
            }
        };

        // ==========================================
        // 5.2 日志中心
        // ==========================================
        const logCenterState = reactive({
            loading: false,
            summary: null,
            category: 'all',
            level: 'all',
            limit: 250,
            hours: 0,
            expanded: {}
        });

        const logCategoryOptions = [
            { value: 'all', label: '全部日志' },
            { value: 'system', label: '系统日志' },
            { value: 'cover', label: '封面系统' },
            { value: 'webhook', label: 'Webhook' },
            { value: 'notify', label: '通知日志' },
            { value: 'emby', label: 'Emby' }
        ];

        const logLevelOptions = [
            { value: 'all', label: '全部级别' },
            { value: 'ERROR', label: 'ERROR' },
            { value: 'WARNING', label: 'WARNING' },
            { value: 'INFO', label: 'INFO' },
            { value: 'DEBUG', label: 'DEBUG' }
        ];

        const logTimeOptions = [
            { value: 0, label: '全部日志' },
            { value: 24, label: '最近 24 小时' }
        ];

        const fetchLogCenter = async () => {
            logCenterState.loading = true;
            try {
                const res = await axios.get('/api/logs/summary', {
                    params: {
                        limit: logCenterState.limit,
                        category: logCenterState.category,
                        level: logCenterState.level,
                        hours: logCenterState.hours
                    }
                });
                logCenterState.summary = res.data;
            } catch (e) {
                showToast(apiErrorMessage(e, '日志读取失败'), 'error');
            } finally {
                logCenterState.loading = false;
            }
        };

        const toggleLogEntryDetail = (entry) => {
            if (!entry) return;
            logCenterState.expanded[entry.id] = !logCenterState.expanded[entry.id];
        };

        watch(() => [logCenterState.category, logCenterState.level, logCenterState.limit, logCenterState.hours], () => {
            if (tab.value === 'logs') fetchLogCenter();
            if (consoleLogState.visible) fetchSystemLogs(true);
        });

        // ==========================================
        // 5.3 配置助手
        // ==========================================
        const configAssistantState = reactive({
            loading: false,
            summary: null
        });

        const fetchConfigAssistant = async () => {
            configAssistantState.loading = true;
            try {
                const res = await axios.get('/api/config_assistant/summary');
                configAssistantState.summary = res.data;
            } catch (e) {
                showToast(apiErrorMessage(e, '配置助手读取失败'), 'error');
            } finally {
                configAssistantState.loading = false;
            }
        };

        const configStatusMeta = (status) => {
            const map = {
                ok: { label: '正常', icon: 'fa-circle-check' },
                warning: { label: '建议处理', icon: 'fa-triangle-exclamation' },
                critical: { label: '需要处理', icon: 'fa-circle-xmark' },
                info: { label: '可选', icon: 'fa-circle-info' }
            };
            return map[status] || map.info;
        };

        const jumpToConfigTarget = (targetTab) => {
            if (!targetTab) return;
            tab.value = targetTab;
        };

        // ==========================================
        // 5.4 Emby 实用工具接口
        // ==========================================
        const mediaToolsState = reactive({
            loading: false,
            serverIdx: 0,
            libraryId: '',
            query: '',
            itemType: 'Movie,Series',
            issueFilter: 'all',
            limit: 30,
            lastReadAt: '',
            result: null
        });

        const mediaIssueOptions = [
            { value: 'all', label: '全部' },
            { value: 'action_required', label: '待处理' },
            { value: 'critical', label: '严重问题' },
            { value: 'missing_tmdb', label: '缺 TMDb' },
            { value: 'missing_imdb', label: '缺 IMDb' },
            { value: 'missing_overview', label: '缺简介' },
            { value: 'missing_primary', label: '缺封面' },
            { value: 'missing_path', label: '缺路径' },
            { value: 'missing_file', label: '疑似缺文件' },
            { value: 'has_4k', label: '4K 条目' }
        ];

        const mediaTypeOptions = [
            { value: 'Movie,Series', label: '电影 + 剧集' },
            { value: 'Movie', label: '电影' },
            { value: 'Series', label: '剧集' },
            { value: 'BoxSet', label: '合集' }
        ];

        const collectionIssueOptions = [
            { value: 'all', label: '全部' },
            { value: 'action_required', label: '待处理' },
            { value: 'critical', label: '严重问题' },
            { value: 'empty', label: '空合集' },
            { value: 'low_members', label: '成员过少' },
            { value: 'missing_tmdb', label: '缺 TMDb' },
            { value: 'missing_overview', label: '缺简介' },
            { value: 'missing_primary', label: '缺封面' }
        ];

        const embyTasksState = reactive({
            loading: false,
            actionId: '',
            serverIdx: 0,
            categoryFilter: 'all',
            resultFilter: 'all',
            lastReadAt: '',
            result: null
        });

        const collectionsState = reactive({
            loading: false,
            detailLoading: false,
            actionId: '',
            serverIdx: 0,
            query: '',
            issueFilter: 'all',
            minMembers: 2,
            limit: 30,
            lastReadAt: '',
            result: null,
            detail: null
        });

        const embyToolPayload = (idx) => {
            const svr = servers.value[idx];
            if (!svr || !svr.host || !svr.key) {
                throw new Error('请先在 Emby 配置里填写服务器地址和 API Key');
            }
            return embyConnectionPayload(svr);
        };

        const ensureToolLibraries = async (state) => {
            const svr = servers.value[state.serverIdx];
            if (!svr) return [];
            if (!svr.libraries) {
                return await loadLibraries(state.serverIdx);
            }
            return svr.libraries;
        };

        const fetchMediaToolsLibraries = async () => {
            try {
                const libs = await ensureToolLibraries(mediaToolsState);
                if (!mediaToolsState.libraryId && libs.length) mediaToolsState.libraryId = libs[0].id;
            } catch (e) {
                showToast(apiErrorMessage(e, '媒体库列表读取失败'), 'error');
            }
        };

        const runMediaMaintenanceSearch = async () => {
            mediaToolsState.loading = true;
            try {
                const res = await axios.post('/api/emby_tools/media/search', {
                    ...embyToolPayload(mediaToolsState.serverIdx),
                    library_id: mediaToolsState.libraryId || '',
                    query: mediaToolsState.query || '',
                    item_type: mediaToolsState.itemType,
                    issue_filter: mediaToolsState.issueFilter,
                    limit: mediaToolsState.limit
                });
                mediaToolsState.result = res.data;
                mediaToolsState.lastReadAt = new Date().toLocaleTimeString('zh-CN', { hour12: false });
                showToast(`已读取 ${res.data.count || 0} 条媒体记录`, 'success');
            } catch (e) {
                showToast(apiErrorMessage(e, '媒体问题清单读取失败'), 'error');
            } finally {
                mediaToolsState.loading = false;
            }
        };

        const formatMediaSize = (size) => {
            const value = Number(size || 0);
            if (!value) return '';
            const units = ['B', 'KB', 'MB', 'GB', 'TB'];
            let n = value;
            let idx = 0;
            while (n >= 1024 && idx < units.length - 1) {
                n /= 1024;
                idx += 1;
            }
            return `${n.toFixed(idx === 0 ? 0 : 1)} ${units[idx]}`;
        };

        const mediaTypeLabel = (type) => {
            const labels = { Movie: '电影', Series: '剧集', Episode: '单集', BoxSet: '合集' };
            return labels[type] || type || '-';
        };

        const mediaIssueSeverity = (tag) => {
            const map = {
                '疑似文件缺失': 'critical',
                '缺路径': 'critical',
                '空合集': 'critical',
                '成员过少': 'warning',
                '缺封面': 'warning',
                '缺简介': 'warning',
                '缺 TMDb': 'warning',
                '缺 IMDb': 'warning',
                '4K': 'info'
            };
            return map[tag] || 'warning';
        };

        const mediaSeverityMeta = (severity) => {
            const map = {
                critical: { label: '严重', icon: 'fa-circle-exclamation' },
                warning: { label: '建议处理', icon: 'fa-triangle-exclamation' },
                info: { label: '信息', icon: 'fa-circle-info' },
                ok: { label: '正常', icon: 'fa-circle-check' }
            };
            return map[severity] || map.warning;
        };

        const mediaItemSeverity = (item) => item?.issue_meta?.severity || (item?.issues?.length ? 'warning' : 'ok');
        const collectionItemSeverity = (item) => item?.issue_meta?.severity || (item?.issues?.length ? 'warning' : 'ok');

        const issueBlueprintTone = (severity) => ({
            critical: { label: '严重', icon: 'fa-circle-exclamation' },
            warning: { label: '建议处理', icon: 'fa-triangle-exclamation' },
            info: { label: '信息', icon: 'fa-circle-info' },
            ok: { label: '正常', icon: 'fa-circle-check' }
        }[severity] || { label: '建议处理', icon: 'fa-triangle-exclamation' });

        const mediaIssueBlueprint = computed(() => [
            {
                severity: 'critical',
                title: '路径与文件问题',
                tags: '缺路径 / 疑似文件缺失',
                detail: '优先排查，通常影响播放、真实库路径或后续整理。'
            },
            {
                severity: 'warning',
                title: '元数据缺项',
                tags: '缺封面 / 缺简介 / 缺 TMDb / 缺 IMDb',
                detail: '适合批量导出后逐项补全，必要时提交单条刷新。'
            },
            {
                severity: 'info',
                title: '信息标签',
                tags: '4K 条目',
                detail: '只做识别和筛选，不计入待处理问题。'
            }
        ].map(item => ({ ...item, meta: issueBlueprintTone(item.severity) })));

        const collectionIssueBlueprint = computed(() => [
            {
                severity: 'critical',
                title: '空合集',
                tags: '0 个成员',
                detail: '优先处理，通常代表合集失效、误建或成员关联丢失。'
            },
            {
                severity: 'warning',
                title: '成员过少',
                tags: `少于 ${collectionsState.minMembers || 2} 个成员`,
                detail: '适合检查是否只剩残缺成员，阈值可按你的库规模调整。'
            },
            {
                severity: 'warning',
                title: '合集资料缺项',
                tags: '缺封面 / 缺简介 / 缺 TMDb',
                detail: '用于定位需要补图、补说明或重新刮削的合集。'
            }
        ].map(item => ({ ...item, meta: issueBlueprintTone(item.severity) })));

        const mediaResultAdvice = computed(() => {
            const summary = mediaToolsState.result?.summary;
            if (!summary) return '';
            if ((summary.critical || 0) > 0) return '建议先切换到“严重问题”，优先处理缺路径或疑似缺文件条目。';
            if ((summary.warning || 0) > 0) return '当前主要是元数据缺项，可导出 CSV 后按库或类型逐步补全。';
            if ((summary.info || 0) > 0) return '当前只有信息标签，没有必须处理的问题。';
            return '当前结果基础信息完整。';
        });

        const collectionResultAdvice = computed(() => {
            const issues = collectionsState.result?.summary?.issues;
            if (!issues) return '';
            if ((issues.critical || 0) > 0) return '建议先处理空合集，确认是删除、重新关联成员，还是等待 Emby 扫描恢复。';
            if ((issues.warning || 0) > 0) return '当前主要是成员过少或资料缺项，可先查看成员，再决定是否刷新元数据。';
            return '当前合集基础信息完整。';
        });

        const copyMediaPath = async (item) => {
            if (!item?.path) {
                showToast('这个条目没有可复制的路径', 'warning');
                return;
            }
            try {
                await navigator.clipboard.writeText(item.path);
                showToast('路径已复制', 'success');
            } catch (e) {
                showToast('复制失败，请手动复制', 'error');
            }
        };

        const openEmbyItem = (item) => {
            if (!item?.emby_url) {
                showToast('没有可打开的 Emby 地址', 'warning');
                return;
            }
            window.open(item.emby_url, '_blank', 'noopener,noreferrer');
        };

        const exportMediaMaintenanceCsv = () => {
            const rows = mediaToolsState.result?.items || [];
            if (!rows.length) {
                showToast('没有可导出的记录', 'warning');
                return;
            }
            const escapeCell = (value) => `"${String(value ?? '').replace(/"/g, '""')}"`;
            const header = ['名称', '类型', '年份', '严重程度', '待处理问题', '全部标签', 'TMDb', 'IMDb', '分辨率', '大小', '路径', 'Emby'];
            const csvRows = rows.map(item => [
                item.name,
                mediaTypeLabel(item.type),
                item.year || '',
                mediaSeverityMeta(mediaItemSeverity(item)).label,
                (item.issue_meta?.actionable_issues || []).join(' / ') || '无待处理问题',
                (item.issues || []).join(' / ') || '基础信息完整',
                item.tmdb || '',
                item.imdb || '',
                item.height ? `${item.height}p` : '',
                formatMediaSize(item.size),
                item.path || '',
                item.emby_url || ''
            ].map(escapeCell).join(','));
            const blob = new Blob([`\uFEFF${header.map(escapeCell).join(',')}\n${csvRows.join('\n')}`], { type: 'text/csv;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `alsemby-media-maintenance-${Date.now()}.csv`;
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(url);
            showToast('维护清单已导出', 'success');
        };

        const refreshMediaMetadata = async (item, refreshImages = false) => {
            const ok = await showConfirm(
                '刷新元数据',
                `确定提交 "${item?.name || '当前条目'}" 的 Emby 元数据刷新任务吗？这只处理单个条目，不会批量刷新。`,
                'warning'
            );
            if (!ok) return;
            try {
                await axios.post('/api/emby_tools/media/refresh', {
                    ...embyToolPayload(mediaToolsState.serverIdx),
                    item_id: item.id,
                    item_name: item.name,
                    refresh_images: refreshImages,
                    confirm: true
                });
                showToast('已提交 Emby 刷新任务', 'success');
            } catch (e) {
                showToast(apiErrorMessage(e, '提交刷新失败'), 'error');
            }
        };

        const fetchEmbyTasksLibraries = async () => {
            try {
                await ensureToolLibraries(embyTasksState);
            } catch (e) {
                showToast(apiErrorMessage(e, 'Emby 服务器准备失败'), 'error');
            }
        };

        const fetchEmbyScheduledTasks = async () => {
            embyTasksState.loading = true;
            try {
                const res = await axios.post('/api/emby_tools/tasks/list', embyToolPayload(embyTasksState.serverIdx));
                embyTasksState.result = res.data;
                embyTasksState.lastReadAt = new Date().toLocaleTimeString('zh-CN', { hour12: false });
                showToast(`已读取 ${res.data.count || 0} 个 Emby 计划任务`, 'success');
            } catch (e) {
                showToast(apiErrorMessage(e, 'Emby 任务读取失败'), 'error');
            } finally {
                embyTasksState.loading = false;
            }
        };

        const embyTaskStateLabel = (state) => {
            const labels = { Idle: '空闲', Running: '运行中', Cancelling: '停止中' };
            return labels[state] || state || '-';
        };

        const embyTaskLastResult = (task) => {
            const result = task?.last_execution_result || {};
            if (!result.Status && !result.EndTimeUtc) return '暂无运行记录';
            const status = embyTaskLastResultStatusLabel(task);
            const end = result.EndTimeUtc ? result.EndTimeUtc.replace('T', ' ').replace('Z', '') : '';
            return `${status}${end ? ` · ${end}` : ''}`;
        };

        const embyTaskLastResultStatus = (task) => {
            return String(task?.last_execution_result?.Status || '').trim();
        };

        const embyTaskLastResultStatusLabel = (task) => {
            const status = embyTaskLastResultStatus(task);
            const labels = {
                Completed: '完成',
                Failed: '失败',
                Cancelled: '已取消',
                Aborted: '已中止',
                Running: '运行中',
                Unknown: '未知',
            };
            return labels[status] || status || '暂无';
        };

        const embyTaskResultTone = (task) => {
            const status = embyTaskLastResultStatus(task).toLowerCase();
            if (!status) return 'muted';
            if (['completed', 'success', 'succeeded'].includes(status)) return 'success';
            if (status.includes('fail') || status.includes('error')) return 'error';
            if (status.includes('cancel') || status.includes('abort')) return 'warning';
            return 'info';
        };

        const embyTaskResultIcon = (task) => {
            const tone = embyTaskResultTone(task);
            return {
                success: 'fa-circle-check',
                error: 'fa-circle-xmark',
                warning: 'fa-triangle-exclamation',
                info: 'fa-circle-info',
                muted: 'fa-minus-circle',
            }[tone] || 'fa-circle-info';
        };

        const isEmbyTaskFailed = (task) => embyTaskResultTone(task) === 'error';

        const embyTaskMatchesResultFilter = (task) => {
            if (embyTasksState.resultFilter === 'running') return task.state === 'Running';
            if (embyTasksState.resultFilter === 'failed') return isEmbyTaskFailed(task);
            if (embyTasksState.resultFilter === 'idle') return task.state !== 'Running';
            return true;
        };

        const embyTaskCategoryScopedTasks = computed(() => {
            const tasks = embyTasksState.result?.tasks || [];
            return tasks.filter(task => (
                embyTasksState.categoryFilter === 'all' || task.category === embyTasksState.categoryFilter
            ));
        });

        const embyTaskVisibleTasks = computed(() => {
            return embyTaskCategoryScopedTasks.value.filter(embyTaskMatchesResultFilter);
        });

        const embyTaskGroups = computed(() => {
            const tasks = embyTaskVisibleTasks.value;
            const groups = [];
            const map = new Map();
            tasks.forEach(task => {
                const name = task.category || 'Other';
                if (!map.has(name)) {
                    const group = { name, tasks: [] };
                    map.set(name, group);
                    groups.push(group);
                }
                map.get(name).tasks.push(task);
            });
            return groups;
        });

        const embyTaskResultFilters = computed(() => {
            const tasks = embyTaskCategoryScopedTasks.value;
            return [
                { name: 'all', label: '全部结果', count: tasks.length, icon: 'fa-list-check' },
                { name: 'running', label: '运行中', count: tasks.filter(task => task.state === 'Running').length, icon: 'fa-play' },
                { name: 'failed', label: '最近失败', count: tasks.filter(isEmbyTaskFailed).length, icon: 'fa-triangle-exclamation' },
                { name: 'idle', label: '空闲', count: tasks.filter(task => task.state !== 'Running').length, icon: 'fa-pause' },
            ];
        });

        const embyTaskCategoryFilters = computed(() => {
            const categories = embyTasksState.result?.categories || [];
            const total = embyTasksState.result?.count || 0;
            return [
                { name: 'all', label: '全部', count: total, icon: 'fa-layer-group' },
                ...categories.map(item => ({
                    name: item.name,
                    label: embyTaskCategoryLabel(item.name),
                    count: item.count,
                    icon: embyTaskGroupIcon(item.name)
                }))
            ];
        });

        const embyTaskRunningCount = computed(() => {
            const tasks = embyTasksState.result?.tasks || [];
            return tasks.filter(task => task.state === 'Running').length;
        });

        const embyTaskFailedCount = computed(() => {
            const tasks = embyTasksState.result?.tasks || [];
            return tasks.filter(isEmbyTaskFailed).length;
        });

        const embyTaskVisibleCount = computed(() => embyTaskVisibleTasks.value.length);

        const embyTaskShenyiCount = computed(() => {
            const tasks = embyTasksState.result?.tasks || [];
            return tasks.filter(task => task.category === '神医助手').length;
        });

        const embyTaskCategoryLabel = (name) => {
            const labels = {
                Application: 'Application',
                Database: 'Database',
                'Downloads & Conversions': 'Downloads & Conversions',
                'Infuse Sync': 'Infuse Sync',
                Library: 'Library',
                '神医助手': '神医助手 💎 PRO',
                Other: 'Other'
            };
            return labels[name] || name || 'Other';
        };

        const embyTaskGroupDescription = (name) => {
            const descriptions = {
                Application: '日志轮转、应用级维护等基础任务。',
                Database: '数据库整理、Vacuum 等低频维护任务。',
                'Downloads & Conversions': '转码、下载转换和转移类任务。',
                'Infuse Sync': 'Infuse 同步缓存与旧数据清理任务。',
                Library: '媒体库扫描、字幕、元数据和缩略图任务。',
                '神医助手': '插件增强任务，包含豆瓣缓存、媒体信息、演员、剧集和外挂轨道等维护。',
                Other: 'Emby 返回但未归入固定分组的任务。'
            };
            return descriptions[name] || 'Emby 返回的计划任务分组。';
        };

        const embyTaskGroupIcon = (name) => {
            const icons = {
                Application: 'fa-window-maximize',
                Database: 'fa-database',
                'Downloads & Conversions': 'fa-right-left',
                'Infuse Sync': 'fa-rotate',
                Library: 'fa-folder-open',
                '神医助手': 'fa-wand-magic-sparkles',
                Other: 'fa-list-check'
            };
            return icons[name] || 'fa-list-check';
        };

        const embyTaskBlueprint = computed(() => [
            'Application',
            'Database',
            'Downloads & Conversions',
            'Infuse Sync',
            'Library',
            '神医助手',
            'Other'
        ].map((name) => ({
            name,
            label: embyTaskCategoryLabel(name),
            icon: embyTaskGroupIcon(name),
            description: embyTaskGroupDescription(name),
            count: embyTasksState.result?.categories?.find(item => item.name === name)?.count || 0
        })));

        const openEmbyTaskLogs = (level = 'all') => {
            logCenterState.category = 'emby';
            logCenterState.level = level;
            logCenterState.hours = 0;
            selectBottomTab('logs');
            fetchLogCenter();
        };

        const runEmbyScheduledTask = async (task) => {
            const ok = await showConfirm(
                '运行 Emby 任务',
                `确定立即运行 "${task?.name || '当前任务'}" 吗？这会直接请求 Emby 后台任务接口。`,
                'warning'
            );
            if (!ok) return;
            embyTasksState.actionId = task.id;
            try {
                await axios.post('/api/emby_tools/tasks/run', {
                    ...embyToolPayload(embyTasksState.serverIdx),
                    task_id: task.id,
                    task_name: task.name,
                    confirm: true
                });
                showToast('已提交 Emby 任务运行请求', 'success');
                await fetchEmbyScheduledTasks();
            } catch (e) {
                showToast(apiErrorMessage(e, '运行 Emby 任务失败'), 'error');
            } finally {
                embyTasksState.actionId = '';
            }
        };

        const stopEmbyScheduledTask = async (task) => {
            const ok = await showConfirm(
                '停止 Emby 任务',
                `确定请求停止 "${task?.name || '当前任务'}" 吗？只有正在运行的 Emby 任务才会响应。`,
                'danger'
            );
            if (!ok) return;
            embyTasksState.actionId = task.id;
            try {
                await axios.post('/api/emby_tools/tasks/stop', {
                    ...embyToolPayload(embyTasksState.serverIdx),
                    task_id: task.id,
                    task_name: task.name,
                    confirm: true
                });
                showToast('已提交 Emby 任务停止请求', 'success');
                await fetchEmbyScheduledTasks();
            } catch (e) {
                showToast(apiErrorMessage(e, '停止 Emby 任务失败'), 'error');
            } finally {
                embyTasksState.actionId = '';
            }
        };

        const fetchCollectionLibraries = async () => {
            try {
                await ensureToolLibraries(collectionsState);
            } catch (e) {
                showToast(apiErrorMessage(e, '合集问题清单准备失败'), 'error');
            }
        };

        const fetchCollectionSummary = async () => {
            collectionsState.loading = true;
            try {
                const res = await axios.post('/api/emby_tools/collections/summary', {
                    ...embyToolPayload(collectionsState.serverIdx),
                    query: collectionsState.query || '',
                    issue_filter: collectionsState.issueFilter,
                    min_members: collectionsState.minMembers,
                    limit: collectionsState.limit
                });
                collectionsState.result = res.data;
                collectionsState.lastReadAt = new Date().toLocaleTimeString('zh-CN', { hour12: false });
                collectionsState.detail = null;
                showToast(`已读取 ${res.data.count || 0} 个合集`, 'success');
            } catch (e) {
                showToast(apiErrorMessage(e, '合集问题清单读取失败'), 'error');
            } finally {
                collectionsState.loading = false;
            }
        };

        const exportCollectionCsv = () => {
            const rows = collectionsState.result?.collections || [];
            if (!rows.length) {
                showToast('没有可导出的合集记录', 'warning');
                return;
            }
            const escapeCell = (value) => `"${String(value ?? '').replace(/"/g, '""')}"`;
            const header = ['合集名', '严重程度', '成员数', '待处理问题', '全部标签', 'TMDb', '有简介', '有封面', 'Emby'];
            const csvRows = rows.map(item => [
                item.name,
                mediaSeverityMeta(collectionItemSeverity(item)).label,
                item.count ?? 0,
                (item.issue_meta?.actionable_issues || []).join(' / ') || '无待处理问题',
                (item.issues || []).join(' / ') || '基础信息完整',
                item.tmdb || '',
                item.overview ? '是' : '否',
                item.has_primary ? '是' : '否',
                item.emby_url || ''
            ].map(escapeCell).join(','));
            const blob = new Blob([`\uFEFF${header.map(escapeCell).join(',')}\n${csvRows.join('\n')}`], { type: 'text/csv;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `alsemby-collections-${Date.now()}.csv`;
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(url);
            showToast('合集清单已导出', 'success');
        };

        const fetchCollectionItems = async (item) => {
            collectionsState.detailLoading = true;
            try {
                const res = await axios.post('/api/emby_tools/collections/items', {
                    ...embyToolPayload(collectionsState.serverIdx),
                    collection_id: item.id,
                    limit: 80
                });
                collectionsState.detail = {
                    collection: item,
                    ...res.data
                };
                showToast(`已读取 ${res.data.count || 0} 个合集成员`, 'success');
            } catch (e) {
                showToast(apiErrorMessage(e, '合集成员读取失败'), 'error');
            } finally {
                collectionsState.detailLoading = false;
            }
        };

        const refreshCollectionMetadata = async (item) => {
            const ok = await showConfirm(
                '刷新合集元数据',
                `确定提交 "${item?.name || '当前合集'}" 的 Emby 元数据刷新任务吗？这只处理单个合集。`,
                'warning'
            );
            if (!ok) return;
            collectionsState.actionId = item.id;
            try {
                await axios.post('/api/emby_tools/media/refresh', {
                    ...embyToolPayload(collectionsState.serverIdx),
                    item_id: item.id,
                    item_name: item.name,
                    refresh_images: true,
                    confirm: true
                });
                showToast('已提交合集刷新任务', 'success');
            } catch (e) {
                showToast(apiErrorMessage(e, '提交合集刷新失败'), 'error');
            } finally {
                collectionsState.actionId = '';
            }
        };

        watch(() => webhookConfig.engine, (newVal) => {
            if (!newVal) return;
            const currentPreset = presetList.value.find(p => p.filename === webhookConfig.preset);
            if (!webhookConfig.preset || (currentPreset && currentPreset.engine !== newVal)) {
                const available = presetList.value.filter(p => p.engine === newVal);
                if (available.length > 0) {
                    webhookConfig.preset = available[0].filename;
                } else {
                    webhookConfig.preset = '';
                }
            }
        });

        // 监听 tab 变化，仪表盘恢复时重启海报墙动画
        watch(tab, () => {
            if (tab.value === 'dashboard') {
                setTimeout(() => {
                    const wallTracks = document.querySelectorAll('.wall-track');
                    wallTracks.forEach(track => {
                        track.style.animation = 'none';
                        track.offsetHeight; // 触发重排
                        track.style.animation = '';
                    });
                }, 100);
            }
        });

        onMounted(() => {
            // 延迟触发海报滚动动画，确保数据加载完成
            setTimeout(() => {
                const wallTracks = document.querySelectorAll('.wall-track');
                wallTracks.forEach(track => {
                    // 通过重置 animation 来强制触发动画
                    track.style.animation = 'none';
                    track.offsetHeight; // 触发重排
                    track.style.animation = '';
                });
            }, 300);
        });

        axios.interceptors.request.use(cfg => cfg, error => Promise.reject(error));

        const filteredPresets = computed(() => {
            if (!config.engine) return [];
            return presetList.value.map((p, index) => ({ ...p, originalIndex: index })).filter(p => p.engine === config.engine);
        });
        const manualPresetOptions = computed(() => {
            if (config.engine !== '自由设计') return filteredPresets.value;
            const baseFile = manualDesignerBaseFile.value;
            if (!baseFile) return [];
            return presetList.value
                .map((preset, originalIndex) => ({ ...preset, originalIndex }))
                .filter(preset => preset.engine === '自由设计'
                    && (preset.filename === baseFile || preset.config?.designer_parent === baseFile))
                .map(preset => ({
                    ...preset,
                    displayName: preset.filename === baseFile ? `${preset.name}默认` : preset.name
                }));
        });
        const userDesignerLayoutOptions = computed(() => presetList.value
            .map((preset, originalIndex) => ({ ...preset, originalIndex }))
            .filter(preset => isDesignerLayoutPreset(preset) && !preset.is_builtin)
            .map(preset => ({
                ...preset,
                value: `designer:${preset.filename}`,
                label: preset.name
            })));
        const manualLayoutSelection = computed({
            get: () => {
                if (config.engine !== '自由设计') return config.engine;
                const option = userDesignerLayoutOptions.value.find(item => item.filename === manualDesignerBaseFile.value);
                return option?.value || '';
            },
            set: (value) => {
                if (String(value).startsWith('designer:')) {
                    const filename = String(value).slice('designer:'.length);
                    const option = userDesignerLayoutOptions.value.find(item => item.filename === filename);
                    if (!option) return;
                    manualDesignerBaseFile.value = filename;
                    selectedPresetIdx.value = option.originalIndex;
                    loadPreset();
                    return;
                }
                currentPresetFile.value = '';
                manualDesignerBaseFile.value = '';
                config.engine = value;
            }
        });
        const activeManualLayoutLabel = computed(() => {
            if (config.engine !== '自由设计') return `${layoutLabel(config.engine)}模式`;
            return userDesignerLayoutOptions.value.find(item => item.filename === manualDesignerBaseFile.value)?.label || '自定义模式';
        });

        const currentSchema = computed(() => layoutSchemas.value[config.engine] || []);

        const initGradientConfig = (prefix, solidColor) => {
            const defaults = prefix === 'subtitle'
                ? ['#dbeafe', '#c4b5fd', '#f9a8d4']
                : ['#ffffff', '#5eead4', '#60a5fa'];
            if (config[`${prefix}_color_mode`] === undefined) config[`${prefix}_color_mode`] = 'solid';
            if (config[`${prefix}_gradient_start`] === undefined) config[`${prefix}_gradient_start`] = solidColor || defaults[0];
            if (config[`${prefix}_gradient_middle`] === undefined) config[`${prefix}_gradient_middle`] = defaults[1];
            if (config[`${prefix}_gradient_end`] === undefined) config[`${prefix}_gradient_end`] = defaults[2];
            if (config[`${prefix}_gradient_direction`] === undefined) config[`${prefix}_gradient_direction`] = 'horizontal';
        };

        const pageTitle = computed(() => {
            const map = {
                'dashboard': '仪表盘', 'manual':'封面创作', 'custom':'自由设计', 'auto':'自动封面',
                'tools': '工具系统', 'rss': 'RSS 真实库', 'webhook': 'Webhook',
                'media_maintenance': '媒体问题清单', 'emby_tasks': 'Emby 任务中心', 'collections': '合集问题清单',
                'diagnostics': '诊断助手', 'logs': '日志中心', 'config_assistant': '配置助手',
                'server':'Emby 配置', 'fonts':'字体管理', 'templates':'模板管理',
                'library_preview':'封面备份', 'translations':'封面标题', 'account':'账户管理',
                'config_notification': '通知配置'
            };
            return map[tab.value] || '仪表盘';
        });
        
        const currentManualServer = computed(() => servers.value[manualServerIdx.value] || {});
        const callbackUrl = computed(() => `http://<你的服务器IP或域名>${window.location.port ? ':' + window.location.port : ''}/api/wechat-notify/callback`);

        const fetchCurrentUserInfo = async () => {
            try {
                const res = await axios.get('/api/user_info');
                if (res.data && res.data.username) {
                    currentUsername.value = res.data.username;
                    localStorage.setItem('username', res.data.username);
                }
            } catch (e) { }
        };

        const validateSelections = () => {
            const layouts = layoutList.value;
            if (layouts.length === 0) return;
            if (!taskEngine.value || !layouts.includes(taskEngine.value)) {
                taskEngine.value = layouts[0];
            }
            const taskAvail = presetList.value.filter(p => p.engine === taskEngine.value);
            if (taskAvail.length > 0 && (!taskPreset.value || !taskAvail.find(p=>p.filename===taskPreset.value))) {
                taskPreset.value = taskAvail[0].filename;
            }
            if (!webhookConfig.engine || !layouts.includes(webhookConfig.engine)) {
                webhookConfig.engine = layouts[0];
            }
            const whAvail = presetList.value.filter(p => p.engine === webhookConfig.engine);
            if (whAvail.length > 0 && (!webhookConfig.preset || !whAvail.find(p=>p.filename===webhookConfig.preset))) {
                webhookConfig.preset = whAvail[0].filename;
            }
            if (!config.engine || !layouts.includes(config.engine)) {
                config.engine = layouts[0];
                initLayoutConfig();
            }
        };

        watch(layoutList, (newVal) => { if (newVal && newVal.length > 0) validateSelections(); });
        watch(presetList, (newVal) => { if (newVal && newVal.length > 0) validateSelections(); });

        const sanitizeServers = (rawList) => {
            if (!Array.isArray(rawList)) return [];
            return rawList.map(s => ({
                ...s,
                user_name: s.user_name || '',
                expanded: !!s.expanded, 
                testing: false,
                status: s.status || 'unknown'
            }));
        };

        const embyConnectionPayload = (server = {}) => ({
            host: server.host || '',
            key: server.key || '',
            public_host: server.public_host || '',
            user_name: server.user_name || ''
        });

        const loadTabData = async (val = tab.value) => {
            if (val === 'rss') return fetchRssData();
            if (val === 'tools') return fetchToolsSummary();
            if (val === 'webhook') {
                return fetchWebhookConfig();
            }
            if (val === 'diagnostics') return fetchDiagnosticsSummary();
            if (val === 'logs') return fetchLogCenter();
            if (val === 'config_assistant') return fetchConfigAssistant();
            if (val === 'config_notification') {
                return fetchWechatNotifyConfig();
            }
            if (val === 'media_maintenance') return fetchMediaToolsLibraries();
            if (val === 'emby_tasks') return fetchEmbyTasksLibraries();
            if (val === 'collections') return fetchCollectionLibraries();
            return Promise.resolve();
        };

        const handleGlobalKeydown = (event) => {
            if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
                event.preventDefault();
                commandOpen.value = true;
                nextTick(() => commandInput.value?.focus());
                return;
            }
            if (tab.value !== 'manual' || creationMode.value !== 'designer') return;
            const tag = event.target?.tagName?.toLowerCase();
            if (['input', 'textarea', 'select'].includes(tag)) return;
            if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z') {
                event.preventDefault();
                event.shiftKey ? redoDesigner() : undoDesigner();
                return;
            }
            if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'y') {
                event.preventDefault();
                redoDesigner();
                return;
            }
            if ((event.key === 'Delete' || event.key === 'Backspace') && selectedDesignerElement.value) {
                event.preventDefault();
                removeDesignerElement();
                return;
            }
            const movement = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[event.key];
            if (movement && selectedDesignerElement.value) {
                event.preventDefault();
                const step = event.shiftKey ? 20 : 5;
                const element = selectedDesignerElement.value;
                moveDesignerElement(element, element.x + movement[0] * step, element.y + movement[1] * step);
                commitDesignerHistory();
            }
        };

        onMounted(async () => {
            window.addEventListener('keydown', handleGlobalKeydown);
            const token = localStorage.getItem('authToken');
            if (!localStorage.getItem('isLoggedIn') || !token) {
                localStorage.removeItem('isLoggedIn');
                localStorage.removeItem('authToken');
                window.location.href = 'login.html';
                return;
            }
            axios.defaults.headers.common.Authorization = `Bearer ${token}`;
            syncTabFromHash();
            window.addEventListener('hashchange', syncTabFromHash);

            webhookUrl.value = window.location.origin + '/api/webhook';

            startPolling();
            fetchCurrentUserInfo();
            fetchFonts(); fetchLayouts(); fetchLayoutAndPresets(); fetchSuites(); fetchTranslations(); fetchTasks(); fetchDashboardStats();
            fetchWebhookConfig();
            resetDesignerHistory();
            
            try { 
                const res = await axios.get('/api/load'); 
                if (res.data) {
                    if (res.data.servers) {
                        servers.value = sanitizeServers(res.data.servers);
                        if (tab.value === 'dashboard') await initDashboard();
                        const activeServer = servers.value[manualServerIdx.value];
                        if (activeServer?.host && activeServer?.key) {
                            // Server-side library permissions can change while the
                            // saved list remains cached. Refresh it before manual
                            // preview so stale IDs cannot produce a blank cover.
                            await fetchLibs(manualServerIdx.value);
                        }
                    }
                } else {
                    loadLocal(); 
                }
            } catch {
                loadLocal();
                const activeServer = servers.value[manualServerIdx.value];
                if (activeServer?.host && activeServer?.key) await fetchLibs(manualServerIdx.value);
            }

            await loadTabData();
        });

        watch(tab, (next) => {
            const nextHash = next === 'dashboard' ? '' : `#${next}`;
            if (window.location.hash !== nextHash) history.replaceState(null, '', `${window.location.pathname}${nextHash}`);
        });

        onUnmounted(() => {
            window.removeEventListener('hashchange', syncTabFromHash);
            window.removeEventListener('keydown', handleGlobalKeydown);
            stopPolling();
        });

        const loadLocal = () => { 
            const s = localStorage.getItem('emby_servers'); 
            if(s) {
                try {
                    const parsed = JSON.parse(s);
                    servers.value = sanitizeServers(parsed);
                    if (tab.value === 'dashboard') initDashboard();
                } catch(e) { console.error("Load local servers error", e); }
            }
        };

        const initDashboard = async () => {
            if (servers.value.length === 0) return;
            const svr = servers.value[0];
            if (!svr.host || !svr.key) return;

            try {
                const res = await axios.post('/api/library_covers', embyConnectionPayload(svr));
                dashboardCovers.value = res.data.libraries || [];
                if (res.data.libraries) {
                    const simpleLibs = res.data.libraries.map(l => ({ id: l.id, name: l.name }));
                    svr.libraries = simpleLibs;
                    localStorage.setItem('emby_servers', JSON.stringify(servers.value));
                }
                splitIntoRows();
            } catch (e) { console.log("Dashboard init failed", e); }
        };

        const splitIntoRows = () => {
            const covers = dashboardCovers.value;
            if (!covers.length) return;
            const minItems = 10;
            const rows = [[], [], []];
            covers.forEach((item, idx) => { rows[idx % 3].push(item); });
            [0, 1, 2].forEach(i => {
                let current = [...rows[i]];
                if (current.length === 0) current = [...covers]; 
                while (current.length < minItems) current = [...current, ...current];
                wallRows[i] = [...current, ...current];
            });
        };

        const refreshAllLibraries = async () => {
            for (let i = 0; i < servers.value.length; i++) {
                await fetchLibs(i);
            }
        };

        watch(tab, (newVal) => {
            if (newVal === 'dashboard' && dashboardCovers.value.length === 0) initDashboard();
        });

        const toggleAccordion = (key) => accordions[key] = !accordions[key];
        const toggleTaskLog = () => tasksState.logVisible = !tasksState.logVisible;

        const fetchDashboardStats = async () => {
            try {
                const res = await axios.get('/api/dashboard_stats');
                Object.assign(dashboardStats, res.data);
            } catch {}
        };

        const fetchLayouts = async () => { 
            try { 
                const res = await axios.get('/api/layouts'); 
                const schemas = res.data.layouts;
                Object.values(schemas).forEach(groups => groups.forEach(group => {
                    group.items = group.items.map(item => {
                        if (item.key === 'title_color') return { ...item, type: 'gradient-color', gradientPrefix: 'title' };
                        if (item.key === 'subtitle_color') return { ...item, type: 'gradient-color', gradientPrefix: 'subtitle' };
                        return item;
                    });
                }));
                layoutSchemas.value = schemas;
                const keys = Object.keys(res.data.layouts).sort();
                layoutList.value = keys;
                validateSelections();
            } catch (e) { console.error(e); } 
        }
        
        const initLayoutConfig = () => {
            const schema = layoutSchemas.value[config.engine];
            const baseConfig = { 
                engine: config.engine, badge_style: config.badge_style || 'none', badge_font: config.badge_font || '',
                badge_size: config.badge_size || 40, badge_bg_color: config.badge_bg_color || '#0f172a',
                badge_text_color: config.badge_text_color || '#ffffff', badge_opacity: config.badge_opacity !== undefined ? config.badge_opacity : 255,
                badge_text_color_mode: config.badge_text_color_mode || 'solid',
                badge_text_gradient_start: config.badge_text_gradient_start || '#ffffff', badge_text_gradient_middle: config.badge_text_gradient_middle || '#7dd3fc', badge_text_gradient_end: config.badge_text_gradient_end || '#f0abfc', badge_text_gradient_direction: config.badge_text_gradient_direction || 'horizontal',
                badge_bg_color_mode: config.badge_bg_color_mode || 'solid',
                badge_bg_gradient_start: config.badge_bg_gradient_start || '#22d3ee', badge_bg_gradient_middle: config.badge_bg_gradient_middle || '#6366f1', badge_bg_gradient_end: config.badge_bg_gradient_end || '#ec4899', badge_bg_gradient_direction: config.badge_bg_gradient_direction || 'diagonal_down',
                badge_border_opacity: config.badge_border_opacity !== undefined ? config.badge_border_opacity : 40,
                badge_effect_strength: config.badge_effect_strength !== undefined ? config.badge_effect_strength : 70,
                badge_x_percent: config.badge_x_percent !== undefined ? config.badge_x_percent : 2,
                badge_y_percent: config.badge_y_percent !== undefined ? config.badge_y_percent : 3,
                title: config.title, subtitle: config.subtitle, font_title: config.font_title || '', font_subtitle: config.font_subtitle || ''
            };
            for (const key in config) delete config[key];
            Object.assign(config, baseConfig);
            if (schema) {
                schema.forEach(group => { group.items.forEach(item => {
                    if (config[item.key] === undefined) config[item.key] = item.default;
                    if (item.type === 'gradient-color') initGradientConfig(item.gradientPrefix, item.default);
                }); });
            }
        };

        const tryAutoSelectTaskPreset = () => {
            if (!taskEngine.value) return;
            const available = presetList.value.filter(p => p.engine === taskEngine.value);
            if (available.length > 0) {
                const currentIsAvailable = available.some(p => p.filename === taskPreset.value);
                if (!taskPreset.value || !currentIsAvailable) taskPreset.value = available[0].filename;
            } else taskPreset.value = '';
        };

        const tryAutoSelectPreset = () => {
            if (!config.engine) return;
            const available = presetList.value
                .map((p, index) => ({ ...p, originalIndex: index }))
                .filter(p => p.engine === config.engine && (config.engine !== '自由设计' || isDesignerLayoutPreset(p)));
            if (available.length > 0) { selectedPresetIdx.value = available[0].originalIndex; loadPreset(); } 
            else { selectedPresetIdx.value = ''; initLayoutConfig(); }
        };

        watch(() => config.engine, (newVal, oldVal) => {
            if (newVal === oldVal) return;
            const selectedDesignerPreset = presetList.value.find(item => item.filename === manualDesignerBaseFile.value && item.engine === '自由设计');
            if (newVal === '自由设计' && selectedDesignerPreset) return;
            tryAutoSelectPreset();
        });
        watch(taskEngine, (newVal, oldVal) => { if (newVal !== oldVal) { taskPreset.value = ''; tryAutoSelectTaskPreset(); } });
        watch(showCreateTask, (val) => { if (val && !taskPreset.value) tryAutoSelectTaskPreset(); });

        const fetchLayoutAndPresets = async () => {
            try {
                const res = await axios.get('/api/templates_v2');
                layoutGroups.value = res.data.data;
                presetList.value = res.data.all_raw;
                templatePreviewVersion.value = Date.now();
                validateSelections();
                // 自动选择第一个预设
                tryAutoSelectPreset();
            } catch (e) { console.error(e); }
        };

        const loadPreset = () => { 
            const p = presetList.value[selectedPresetIdx.value]; 
            if (p) { 
                currentPresetFile.value = p.filename; 
                config.engine = p.engine || 'classic'; 
                if (p.engine === '自由设计') {
                    manualDesignerBaseFile.value = p.config?.designer_parent || p.filename;
                } else {
                    manualDesignerBaseFile.value = '';
                }
                initLayoutConfig(); 
                
                // === [修复开始] 暂存当前的标题信息 ===
                const currentTitle = config.title;
                const currentSubtitle = config.subtitle;

                // 旧模板没有角标位置字段时，显式使用渲染器的真实左上角默认值。
                const presetConfig = { ...p.config };
                if (p.engine === '自由设计') {
                    presetConfig.designer_elements = normalizeDesignerElements(JSON.parse(JSON.stringify(p.config.designer_elements || [])));
                    if (!presetConfig.designer_parent) presetConfig.designer_role = 'layout';
                }
                if (presetConfig.badge_size === undefined) presetConfig.badge_size = presetConfig.badge_style === 'ribbon' ? 50 : 40;
                if (presetConfig.badge_x_percent === undefined) presetConfig.badge_x_percent = 2;
                if (presetConfig.badge_y_percent === undefined) presetConfig.badge_y_percent = 3;
                if (presetConfig.badge_opacity === undefined) presetConfig.badge_opacity = 255;
                if (presetConfig.badge_border_opacity === undefined) presetConfig.badge_border_opacity = 40;
                if (presetConfig.badge_effect_strength === undefined) presetConfig.badge_effect_strength = 70;
                ['badge_text', 'badge_bg', 'title', 'subtitle'].forEach(prefix => {
                    if (presetConfig[`${prefix}_color_mode`] === undefined) presetConfig[`${prefix}_color_mode`] = 'solid';
                });
                Object.assign(config, presetConfig); 
                
                // === [修复结束] 如果当前有选中的库，强制还原回当前的标题 ===
                if (currentLibId.value) {
                    config.title = currentTitle;
                    // 如果你希望副标题也跟随媒体库，不随模板改变，加上下面这行：
                    config.subtitle = currentSubtitle;
                }

                if(currentLibId.value) preview(); 
            } 
        }
        
        const saveAsNewPreset = async () => {
            const n = prompt("名称:");
            if (!n) return;
            const payloadConfig = JSON.parse(JSON.stringify(config));
            if (config.engine === '自由设计') {
                payloadConfig.designer_parent = manualDesignerBaseFile.value || currentPresetFile.value;
                delete payloadConfig.designer_role;
            }
            await doSave("preset_" + Date.now() + ".json", n, payloadConfig);
        }
        
        const overwritePreset = async () => { 
            if(currentPresetFile.value) {
                const ok = await showConfirm('覆盖预设', '确定要覆盖当前的预设配置吗？此操作无法撤销。', 'warning');
                if(ok) {
                    const oldName = presetList.value.find(p=>p.filename===currentPresetFile.value).name; 
                    const payloadConfig = JSON.parse(JSON.stringify(config)); 
                    await doSave(currentPresetFile.value, oldName, payloadConfig); 
                }
            } 
        }
        
        const doSave = async (f, n, cfg) => { 
            try{ 
                await axios.post('/api/save_template', { filename:f, name:n, engine:config.engine, config: cfg, image_data: previewImage.value }); 
                showToast('预设保存成功: ' + n, 'success');
                await fetchLayoutAndPresets();
                const savedIndex = presetList.value.findIndex(preset => preset.filename === f);
                if (savedIndex >= 0) {
                    selectedPresetIdx.value = savedIndex;
                    loadPreset();
                }
            }catch{ showToast('保存预设失败', 'error'); } 
        }
        
        const deleteTemplate = async (f) => { 
            const ok = await showConfirm('删除预设', '确定要删除这个预设模板吗？', 'danger');
            if(ok) { 
                await axios.post('/api/delete_template', {filename:f}); 
                selectedTemplates.value = selectedTemplates.value.filter(item => item !== f);
                if (currentDesignerPresetFile.value === f) {
                    currentDesignerPresetFile.value = '';
                    selectedDesignerPreset.value = '';
                }
                showToast('预设已删除', 'success');
                fetchLayoutAndPresets(); 
            } 
        }

        const normalizeTitleMapping = (key, value) => {
            const toText = (val) => String(val || '').trim();
            const libraryName = toText(key);
            if (value && typeof value === 'object' && !Array.isArray(value)) {
                return {
                    key: libraryName,
                    title: toText(value.title),
                    val: toText(value.subtitle || value.val)
                };
            }
            return {
                key: libraryName,
                title: '',
                val: toText(value)
            };
        };

        const findTitleMapping = (libraryName) => {
            return translationList.value.find(t => (t.key || '').trim() === libraryName);
        };

        const loadTransFromLib = async () => {
            const svr = servers.value[transServerIdx.value];
            if (!svr || !svr.host || !svr.key) { showToast("请先配置有效的服务器信息", 'error'); return; }
            try {
                const res = await axios.post('/api/connect', embyConnectionPayload(svr));
                const libs = res.data.libraries || [];
                const savedRes = await axios.get('/api/translations');
                const savedMap = savedRes.data;
                const newList = libs.map(lib => {
                    const saved = normalizeTitleMapping(lib.name, savedMap[lib.name]);
                    return { key: lib.name, title: saved.title, val: saved.val };
                });
                for (const k in savedMap) {
                    if (!newList.find(item => item.key === k)) {
                        newList.push(normalizeTitleMapping(k, savedMap[k]));
                    }
                }
                translationList.value = newList;
                showToast(`已读取 ${libs.length} 个媒体库标题`, 'info');
            } catch (e) { showToast(apiErrorMessage(e, '连接服务器失败'), 'error'); }
        };
        const fetchTranslations = async () => {
            try {
                const res = await axios.get('/api/translations');
                translationList.value = Object.entries(res.data).map(([k, v]) => normalizeTitleMapping(k, v));
            } catch { }
        };
        const saveTranslations = async () => {
            const map = {};
            translationList.value.forEach(item => {
                const key = (item.key || '').trim();
                if (!key) return;
                map[key] = {
                    title: (item.title || '').trim(),
                    subtitle: (item.val || '').trim()
                };
            });
            try { await axios.post('/api/save_translations', { translations: map }); showToast("封面标题配置已保存", 'success'); } catch { }
        };
        const addTransRow = () => translationList.value.push({ key: '', title: '', val: '' });
        const removeTransRow = (idx) => translationList.value.splice(idx, 1);

        const addServer = () => servers.value.push({ name: '', host: '', key: '', public_host: '', user_name: '', status: 'unknown', expanded: true, testing: false });

        const onServerUserNameChange = (idx) => {
            const svr = servers.value[idx];
            if (!svr) return;
            svr.user_name = String(svr.user_name || '').trim();
            svr.status = 'unknown';
            delete svr.libraries;
            if (idx === manualServerIdx.value) {
                currentLibId.value = '';
                clearCoverAssets(false);
            }
        };
        
        const removeServer = async (i) => { 
            const ok = await showConfirm('删除服务器', '确定删除此服务器配置吗？', 'danger');
            if(!ok) return; 
            servers.value.splice(i, 1); 
            localStorage.setItem('emby_servers', JSON.stringify(servers.value)); 
            try { await axios.post('/api/save', { servers: servers.value }); } catch {} 
        };
        
        const testConnection = async (idx) => { 
            const svr = servers.value[idx]; 
            if(!svr) return;
            const target = svr.host || '当前 Emby 地址';
            const ok = await showConfirm('测试 Emby 连接', `将请求 ${target} 并读取媒体库列表，确定继续吗？`, 'warning');
            if(!ok) return;
            svr.testing = true;
            try { 
                await loadLibraries(idx, { selectFirst: true });
                showToast(`连接成功: ${svr.name}`, 'success');
            } catch (e) { svr.status = 'error'; showToast(apiErrorMessage(e, `连接失败: ${svr.name}`), 'error');
            } finally { svr.testing = false; } 
        }
        
        const saveAllConfigs = async () => { 
            localStorage.setItem('emby_servers', JSON.stringify(servers.value)); 
            try { await axios.post('/api/save', { servers: servers.value }); showToast('服务器配置已保存', 'success'); } catch { showToast('服务器保存失败', 'error'); } 
        }

        const loadLibraries = async (idx, opts = {}) => {
            const svr = servers.value[idx];
            if (!svr) throw new Error('服务器配置不存在');
            if (!svr.host || !svr.key) throw new Error('请先填写 Emby 地址和 API Key');
            const res = await axios.post('/api/connect', embyConnectionPayload(svr));
            svr.libraries = res.data.libraries || [];
            svr.status = 'ok';
            localStorage.setItem('emby_servers', JSON.stringify(servers.value));
            if (opts.selectFirst && idx === manualServerIdx.value && svr.libraries.length > 0) {
                const stillExists = svr.libraries.some(lib => lib.id === currentLibId.value);
                if (!currentLibId.value || !stillExists) {
                    currentLibId.value = svr.libraries[0].id;
                    onLibChange();
                }
            }
            return svr.libraries;
        };

        const fetchLibs = async (idx) => {
            const svr = servers.value[idx];
            if (!svr) return;
            svr.testing = true;
            try {
                const libs = await loadLibraries(idx, { selectFirst: true });
                showToast(`已读取 ${libs.length} 个媒体库`, 'success');
            } catch (e) {
                showToast(apiErrorMessage(e, '读取媒体库失败'), 'error');
            } finally {
                svr.testing = false;
            }
        };
        
        const onManualServerChange = () => { currentLibId.value = ''; clearCoverAssets(false); fetchLibs(manualServerIdx.value); }
        
        const onLibChange = () => { 
            clearCoverAssets(false);
            if (!currentManualServer.value.libraries) return;
            const l = currentManualServer.value.libraries.find(x => x.id === currentLibId.value); 
            if(l) { 
                const trans = findTitleMapping(l.name);
                config.title = (trans && trans.title) ? trans.title : l.name;
                config.subtitle = (trans && trans.val) ? trans.val : '';
                previewImage.value = ''; 
            } 
        }
        
        const getCoverPayload = () => {
            const payloadConfig = creationMode.value === 'designer'
                ? buildDesignerConfig()
                : JSON.parse(JSON.stringify(config));
            const payload = {
                host: currentManualServer.value.host,
                key: currentManualServer.value.key,
                public_host: currentManualServer.value.public_host,
                user_name: currentManualServer.value.user_name || '',
                library_id: currentLibId.value,
                config: payloadConfig,
                mode: manualMode.value
            };
            const customBackground = coverAssets.bg_url;
            if (creationMode.value === 'auto' && (customBackground || coverAssets.posters.length)) {
                payload.custom_assets = {};
                if (customBackground) payload.custom_assets.bg_url = customBackground;
                if (coverAssets.posters.length) payload.custom_assets.posters = [...coverAssets.posters];
            }
            return payload;
        };

        const preview = async () => { 
            if (!currentLibId.value) { showToast('请先选择媒体库', 'error'); return; }
            if (creationMode.value === 'designer' && designerElements.value.length === 0) { showToast('请先在画布中添加图层', 'error'); return; }
            loading.value = true; 
            try { 
                const res = await axios.post('/api/preview', getCoverPayload()); 
                previewImage.value = res.data.image; 
                if (creationMode.value === 'designer') designerStage.value = 'preview';
                showToast('预览已生成', 'success'); 
            } catch (e) { showToast(apiErrorMessage(e, '预览生成失败'), 'error'); } finally { loading.value = false; } 
        }
        
        const apply = async () => { 
            if (!currentLibId.value) { showToast('请先选择媒体库', 'error'); return; }
            if (!previewImage.value) { showToast('请先生成预览封面', 'error'); return; }
            applying.value = true; 
            try { 
                addLog('info', '正在应用封面...');
                showToast('正在应用封面...', 'info');
                const p = getCoverPayload(); p.image_data = previewImage.value; 
                await axios.post('/api/apply', p); 
                addLog('success', '封面已应用'); showToast('封面上传成功', 'success'); 
            } catch (e) { addLog('error', '应用失败'); showToast(apiErrorMessage(e, '应用失败'), 'error'); } finally { applying.value = false; } 
        }

        // [修复] 增加对 idx 的边界检查，防止报错
        const toggleServerExpand = (idx) => { 
            const svr = servers.value[idx]; 
            if (!svr) {
                console.error("Server index out of bound:", idx);
                return;
            }
            svr.expanded = !svr.expanded; 
            if(svr.expanded && !svr.libraries) fetchLibs(idx); 
        }
        

        const isLibSelected = (sIdx, lId) => autoSelections[sIdx]?.includes(lId);
        const toggleLibSelection = (sIdx, lId) => { if(!autoSelections[sIdx]) autoSelections[sIdx] = []; const list = autoSelections[sIdx]; if(list.includes(lId)) list.splice(list.indexOf(lId), 1); else list.push(lId); }
        const isAllSelected = (sIdx) => { const svr = servers.value[sIdx]; if (!svr || !svr.libraries) return false; const sel = autoSelections[sIdx]; return sel && sel.length === svr.libraries.length; };
        const toggleSelectAll = (sIdx) => { const svr = servers.value[sIdx]; if (!svr || !svr.libraries) return; if (isAllSelected(sIdx)) { autoSelections[sIdx] = []; } else { autoSelections[sIdx] = svr.libraries.map(l => l.id); } };

        const getTaskTargets = () => { const t=[]; for(const [k,v] of Object.entries(autoSelections)) { const s=servers.value[k]; if(s&&v) v.forEach(id=>{ const l=s.libraries.find(x=>x.id===id); if(l) t.push({ host:s.host, key:s.key, public_host:s.public_host, user_name:s.user_name || '', library_id:id, library_name:l.name }); }); } return t; }

        const runSavedTask = async (id) => { 
            const ok = await showConfirm('立即运行', '确定要立即触发此自动任务吗？', 'info');
            if(!ok) return; 
            try { 
                tasksState.activeCount++; 
                tasksState.statusText = "准备执行任务..."; 
                await axios.post('/api/run_saved_task', { id: id }); 
                showToast(`任务已提交后台运行`, 'info'); 
            } catch { showToast('请求执行任务失败', 'error'); } 
        };
        
        const editTask = (task) => { editingTaskId.value = task.id; taskName.value = task.name; taskCron.value = task.cron; taskMode.value = task.mode || 'random'; taskFallbackToNextBackdrop.value = task.fallback_to_next_backdrop !== false; showCreateTask.value = true; const presetObj = presetList.value.find(p => p.filename === task.preset); if (presetObj) { taskEngine.value = presetObj.engine; setTimeout(() => taskPreset.value = task.preset, 50); } else { taskPreset.value = task.preset; } for (const key in autoSelections) delete autoSelections[key]; task.targets.forEach(target => { const sIdx = servers.value.findIndex(s => s.host === target.host && (s.user_name || '') === (target.user_name || '')); if (sIdx > -1) { if (!autoSelections[sIdx]) autoSelections[sIdx] = []; autoSelections[sIdx].push(target.library_id); servers.value[sIdx].expanded = true; if (!servers.value[sIdx].libraries) fetchLibs(sIdx); } }); document.querySelector('.content-area').scrollTop = 0; };
        const cancelEdit = () => { editingTaskId.value = null; taskName.value = ''; taskCron.value = ''; taskFallbackToNextBackdrop.value = true; for (const key in autoSelections) delete autoSelections[key]; showCreateTask.value = false; };
        
        const createTask = async () => { 
            if (!taskName.value || !taskCron.value || !taskPreset.value) return showToast("请完善信息", 'error'); 
            const targets = getTaskTargets(); 
            if (!targets.length) return showToast("请选择库", 'error'); 
            try { 
                const payload = { id: editingTaskId.value, name: taskName.value, cron: taskCron.value, preset_filename: taskPreset.value, targets: targets, mode: taskMode.value, fallback_to_next_backdrop: taskFallbackToNextBackdrop.value }; 
                if (editingTaskId.value) { 
                    await axios.post('/api/update_task', payload); 
                    showToast('任务更新成功: ' + taskName.value, 'success'); 
                    cancelEdit(); 
                } else { 
                    await axios.post('/api/create_task', payload); 
                    showToast('任务创建成功: ' + taskName.value, 'success'); 
                    showCreateTask.value = false; 
                } 
                fetchTasks(); fetchDashboardStats(); 
            } catch (e) { showToast("操作失败: " + e, 'error'); } 
        };
        
        const runTaskNow = async () => { 
            if (!taskPreset.value) return showToast("请先选择预设", 'error'); 
            const targets = getTaskTargets(); 
            if (!targets.length) return showToast("请选择库", 'error'); 
            const ok = await showConfirm('批量试运行', `确定要对 ${targets.length} 个媒体库立即执行一次生成吗？`, 'warning');
            if(!ok) return; 
            runningTask.value = true; 
            try { 
                await axios.post('/api/run_task', { preset_filename: taskPreset.value, targets: targets, mode: taskMode.value, fallback_to_next_backdrop: taskFallbackToNextBackdrop.value }); 
                showToast(`手动批量任务已启动`, 'success'); 
            } catch { showToast(`启动失败`, 'error'); } finally { runningTask.value = false; } 
        }
        
        const deleteTask = async (id) => { 
            const ok = await showConfirm('删除任务', '确定要永久删除此自动任务吗？', 'danger');
            if(!ok) return; 
            try { await axios.post('/api/delete_task', { id: id }); showToast('任务已删除', 'success'); fetchTasks(); fetchDashboardStats(); } catch { showToast("删除失败", 'error'); } 
        };
        const fetchTasks = async () => { try { const res = await axios.get('/api/tasks'); taskList.value = res.data.tasks; } catch {} };
        
        const fetchLibraryCovers = async () => {
            const svr = servers.value[previewServerIdx.value];
            if (!svr || !svr.host) return showToast("请先选择有效的服务器", "error");
            const ok = await showConfirm('刷新封面备份列表', `将请求 ${svr.host} 读取媒体库封面列表，确定继续吗？`, 'warning');
            if (!ok) return;
            loadingCovers.value = true;
            try {
                const res = await axios.post("/api/library_covers", embyConnectionPayload(svr));
                const stamp = Date.now();
                libraryCards.value = res.data.libraries.map(lib => {
                    if (lib.cover_url) lib.cover_url += `${lib.cover_url.includes("?") ? "&" : "?"}_t=${stamp}`;
                    return lib;
                });
                showToast(`成功加载 ${res.data.libraries.length} 个媒体库`, "success");
            } catch(e) {
                console.error(e);
                showToast("刷新失败: " + (e.response?.data?.detail || e.message), "error");
            } finally {
                loadingCovers.value = false;
            }
        };
        const fetchSuites = async () => { 
    try { 
        const res = await axios.get('/api/list_suites?_t=' + new Date().getTime()); 
        suiteList.value = res.data.suites; 
        fetchDashboardStats(); 
    } catch {} 
};
        
        const createSuiteBackup = async () => { 
            if(!newSuiteName.value) return showToast('请填写备份名称', 'error');
            const svr = servers.value[previewServerIdx.value];
            if(!svr || !svr.host) return showToast('请先选择有效的服务器', 'error');
            const ok = await showConfirm('创建封面快照', '将读取当前服务器媒体库封面并创建本地快照，确定继续吗？', 'warning');
            if(!ok) return;
            creatingBackup.value = true; tasksState.activeCount = 1; tasksState.statusText = "请求备份中..."; 
            try { 
                await axios.post('/api/create_suite', { ...embyConnectionPayload(svr), suite_name: newSuiteName.value }); 
                newSuiteName.value=''; showToast('备份任务已开始', 'success'); 
            } catch (e) { showToast('备份请求异常: ' + e, 'error'); } finally { creatingBackup.value = false; } 
        }
        
        const deleteSuite = async (n) => { 
            const ok = await showConfirm('删除快照', `确定要删除备份快照 "${n}" 吗？`, 'danger');
            if(ok) { await axios.post('/api/delete_suite', { suite_name: n }); fetchSuites(); } 
        }
        const viewSuite = async (s) => { viewingSuite.value = s; try { const res = await axios.post('/api/get_suite_content', { suite_name: s.name }); viewingSuiteImages.value = res.data.images; selectedRestoreIds.value = res.data.images.map(i=>i.id); } catch{} }
        const closeSuiteView = () => { viewingSuite.value = null; viewingSuiteImages.value = []; }
        const getLibraryName = (id) => { const f = libraryCards.value.find(l=>l.id==id); return f?f.name:id; }
        const toggleRestoreSelect = (id) => { if(selectedRestoreIds.value.includes(id)) selectedRestoreIds.value = selectedRestoreIds.value.filter(x=>x!==id); else selectedRestoreIds.value.push(id); }
        
        const restoreSelected = async () => { 
            const ok = await showConfirm('恢复快照', `确定要恢复 ${selectedRestoreIds.value.length} 个库的封面吗？`, 'warning');
            if(!ok) return; 
            const svr = servers.value[previewServerIdx.value]; 
            try { 
                await axios.post('/api/restore_suite', { ...embyConnectionPayload(svr), suite_name: viewingSuite.value.name, target_ids: selectedRestoreIds.value }); 
                showToast('恢复任务已提交', 'success'); closeSuiteView(); 
            } catch{ showToast('恢复失败', 'error'); } 
        }
        
        const restoreAll = async () => { 
            const ok = await showConfirm('全量恢复', `警告：这将覆盖当前所有库的封面。确定继续吗？`, 'danger');
            if(!ok) return; 
            const svr = servers.value[previewServerIdx.value]; 
            try { 
                await axios.post('/api/restore_suite', { ...embyConnectionPayload(svr), suite_name: viewingSuite.value.name, target_ids: [] }); 
                showToast('全量恢复任务已提交', 'success'); closeSuiteView(); 
            } catch{ showToast('恢复失败', 'error'); } 
        }
        
        const fetchFonts = async () => { try{ fontList.value = (await axios.get('/api/fonts')).data.fonts; if (!config.font_title && fontList.value.length > 0) { config.font_title = fontList.value[0]; config.font_subtitle = fontList.value[0]; config.badge_font = fontList.value[0]; } fetchDashboardStats(); } catch{} }
        const uploadFont = async (e) => { const fd=new FormData(); fd.append("file", e.target.files[0]); await axios.post('/api/upload_font', fd); fetchFonts(); showToast('字体上传成功', 'success'); }
        
        const deleteFont = async (f) => { 
            const ok = await showConfirm('删除字体', `确定要删除字体 ${f} 吗？`, 'danger');
            if(ok) { await axios.post('/api/delete_font', {filename:f}); fetchFonts(); } 
        }

        const toggleTaskStatus = async (task, event) => {
            const newState = event.target.checked;
            // 乐观更新 UI (防止网络延迟导致的卡顿感)
            task.enabled = newState;
            
            try {
                await axios.post('/api/toggle_task', { id: task.id, enabled: newState });
                showToast(newState ? '任务已启用' : '任务已暂停', newState ? 'success' : 'info');
            } catch (e) {
                // 失败回滚
                task.enabled = !newState;
                event.target.checked = !newState;
                showToast('状态切换失败', 'error');
            }
        };

        const toggleRssStatus = async (task, event) => {
            const newState = event.target.checked;
            // 乐观更新
            task.enabled = newState;
            
            try {
                await axios.post('/api/rss/toggle_task', { id: task.id, enabled: newState });
                showToast(newState ? '订阅已启用' : '订阅已暂停', newState ? 'success' : 'info');
            } catch (e) {
                // 失败回滚
                task.enabled = !newState;
                event.target.checked = !newState;
                showToast('状态切换失败', 'error');
            }
        };
        
        const logout = () => {
            localStorage.removeItem('isLoggedIn');
            localStorage.removeItem('authToken');
            localStorage.removeItem('username');
            window.location.href='login.html';
        }
        // ==========================================
        // 微信通知逻辑
        // ==========================================
        const notificationTypes = ref({
            playback: { name: '播放通知', description: '有人播放媒体时发送通知', icon: '🎬' },
            media_added: { name: '入库通知', description: '新媒体添加到媒体库时发送通知', icon: '📚' },
            task_complete: { name: '海报通知', description: '封面生成任务完成时发送通知', icon: '🎨' }
        });

        // 模板可用变量
        const templateVars = {
            media_added: ['title', 'year', 'media_type', 'library_name', 'rating', 'genres', 'overview', 'tagline', 'poster_url', 'now'],
            playback: ['title', 'media_type', 'rating', 'genres', 'overview', 'tagline', 'emby_name', 'user_name', 'client_info', 'client_name', 'device_name', 'device_ip', 'now', 'poster_url']
        };

        // 默认模板
        const defaultTemplates = {
            media_added: {
                title: '《{{ title }}》{% if year %}({{ year }}){% endif %} 已入库 ✅',
                text: '⭐️评分：{{ rating or \'暂无\' }} ｜ 🎬类型：{{ genres or media_type }}{% if tagline %}\n💬标语：{{ tagline }}{% endif %}\n\n📝简介：{{ overview or \'暂无简介\' }}\n\n📁媒体库：{{ library_name }} ｜ 🕐入库时间：{{ now }}'
            },
            playback: {
                title: '🎬 正在播放《{{ title }}》',
                text: '👤播放用户：{{ user_name or \'未知\' }} ｜ 📺设备：{{ device_name or \'未知\' }}\n📱客户端：{{ client_name or client_info or \'未知\' }} ｜ 🌐IP：{{ device_ip or \'未知\' }}\n🖥️服务器：{{ emby_name }} ｜ 🕐时间：{{ now }}\n\n⭐️评分：{{ rating or \'暂无\' }} ｜ 🎬类型：{{ genres or media_type }}{% if tagline %}\n💬标语：{{ tagline }}{% endif %}\n\n📝简介：{{ overview or \'暂无简介\' }}'
            }
        };

        const wechatNotifyConfig = reactive({
            enabled: false,
            name: '企微',
            channel_name: '',
            corp_id: '',
            app_secret: '',
            token: '',
            agent_id: '',
            proxy_url: '',
            encoding_aes_key: '',
            admin_whitelist: '',
            notify_types: {
                playback: true,
                media_added: true,
                task_complete: true
            },
            templates: JSON.parse(JSON.stringify(defaultTemplates)),
            showSecret: false,
            showToken: false,
            showAesKey: false
        });

        const wechatNotifyTesting = ref(false);
        const wechatNotifySending = ref(false);
        const wechatNotifySaving = ref(false);

        const fetchWechatNotifyConfig = async () => {
            try {
                const res = await axios.get('/api/wechat-notify/config');
                const data = res.data;
                wechatNotifyConfig.enabled = data.enabled || false;
                wechatNotifyConfig.name = ['微信', '企业微信'].includes(data.name) ? '企微' : (data.name || '企微');
                wechatNotifyConfig.channel_name = data.channel_name || '';
                wechatNotifyConfig.corp_id = data.corp_id || '';
                wechatNotifyConfig.app_secret = data.app_secret || '';
                wechatNotifyConfig.token = data.token || '';
                wechatNotifyConfig.agent_id = data.agent_id || '';
                wechatNotifyConfig.proxy_url = data.proxy_url || '';
                wechatNotifyConfig.encoding_aes_key = data.encoding_aes_key || '';
                wechatNotifyConfig.admin_whitelist = data.admin_whitelist || '';
                // 确保 notify_types 有默认值
                if (data.notify_types) {
                    wechatNotifyConfig.notify_types = { ...wechatNotifyConfig.notify_types, ...data.notify_types };
                }
                // 加载模板
                if (data.templates) {
                    for (const key of Object.keys(defaultTemplates)) {
                        if (data.templates[key]) {
                            wechatNotifyConfig.templates[key] = { ...defaultTemplates[key], ...data.templates[key] };
                        }
                    }
                }
            } catch(e) {
                console.error('获取企微通知配置失败', e);
            }
        };

        const toggleNotifyType = (typeKey) => {
            if (wechatNotifyConfig.notify_types) {
                wechatNotifyConfig.notify_types[typeKey] = !wechatNotifyConfig.notify_types[typeKey];
            }
        };

        const saveWechatNotifyConfig = async () => {
            wechatNotifySaving.value = true;
            try {
                const payload = {
                    enabled: wechatNotifyConfig.enabled,
                    name: wechatNotifyConfig.name,
                    channel_name: wechatNotifyConfig.channel_name,
                    corp_id: wechatNotifyConfig.corp_id,
                    app_secret: wechatNotifyConfig.app_secret,
                    token: wechatNotifyConfig.token,
                    agent_id: wechatNotifyConfig.agent_id,
                    proxy_url: wechatNotifyConfig.proxy_url,
                    encoding_aes_key: wechatNotifyConfig.encoding_aes_key,
                    admin_whitelist: wechatNotifyConfig.admin_whitelist,
                    notify_types: wechatNotifyConfig.notify_types,
                    templates: sanitizeTemplates(wechatNotifyConfig.templates)
                };
                await axios.post('/api/wechat-notify/config', payload);
                showToast('企微通知配置已保存', 'success');
            } catch(e) {
                showToast('保存失败: ' + (e.response?.data?.detail || e.message), 'error');
            } finally {
                wechatNotifySaving.value = false;
            }
        };

        const testWechatNotify = async () => {
            const ok = await confirmNotificationAction('企业微信', '测试连接');
            if (!ok) return;
            wechatNotifyTesting.value = true;
            try {
                const res = await axios.post('/api/wechat-notify/test');
                if (res.data.status === 'ok') {
                    showToast('连接成功: ' + res.data.message, 'success');
                } else {
                    showToast('连接失败: ' + res.data.message, 'error');
                }
            } catch(e) {
                showToast('测试失败: ' + (e.response?.data?.detail || e.message), 'error');
            } finally {
                wechatNotifyTesting.value = false;
            }
        };

        const sendWechatTestMsg = async () => {
            const ok = await confirmNotificationAction('企业微信', '发送测试消息');
            if (!ok) return;
            wechatNotifySending.value = true;
            try {
                const res = await axios.post('/api/wechat-notify/send?message=这是一条来自FrameBase的测试消息');
                if (res.data.status === 'ok') {
                    showToast('测试消息发送成功', 'success');
                } else {
                    showToast('发送失败: ' + res.data.message, 'error');
                }
            } catch(e) {
                showToast('发送失败: ' + (e.response?.data?.detail || e.message), 'error');
            } finally {
                wechatNotifySending.value = false;
            }
        };

        const wechatTemplateTesting = ref(false);
        const testWechatTemplate = async () => {
            const ok = await confirmNotificationAction('企业微信', '发送模板测试通知');
            if (!ok) return;
            wechatTemplateTesting.value = true;
            try {
                // 先保存配置确保模板已持久化
                const payload = {
                    enabled: wechatNotifyConfig.enabled,
                    name: wechatNotifyConfig.name,
                    channel_name: wechatNotifyConfig.channel_name,
                    corp_id: wechatNotifyConfig.corp_id,
                    app_secret: wechatNotifyConfig.app_secret,
                    token: wechatNotifyConfig.token,
                    agent_id: wechatNotifyConfig.agent_id,
                    proxy_url: wechatNotifyConfig.proxy_url,
                    encoding_aes_key: wechatNotifyConfig.encoding_aes_key,
                    admin_whitelist: wechatNotifyConfig.admin_whitelist,
                    notify_types: wechatNotifyConfig.notify_types,
                    templates: sanitizeTemplates(wechatNotifyConfig.templates)
                };
                await axios.post('/api/wechat-notify/config', payload);
                const res = await axios.post('/api/wechat-notify/test-template');
                if (res.data.status === 'ok') {
                    showToast('模板测试通知发送成功', 'success');
                } else {
                    showToast('模板测试失败: ' + res.data.message, 'error');
                }
            } catch(e) {
                showToast('模板测试失败: ' + (e.response?.data?.detail || e.message), 'error');
            } finally {
                wechatTemplateTesting.value = false;
            }
        };

        // ==========================================
        // Telegram 通知逻辑
        // ==========================================
        const telegramNotifyConfig = reactive({
            enabled: false,
            name: 'Telegram',
            bot_token: '',
            chat_id: '',
            notify_types: {
                playback: true,
                media_added: true,
                task_complete: true
            },
            templates: JSON.parse(JSON.stringify(defaultTemplates)),
            showToken: false
        });
        const telegramNotifyTesting = ref(false);
        const telegramNotifySending = ref(false);
        const telegramNotifySaving = ref(false);

        const fetchTelegramNotifyConfig = async () => {
            try {
                const res = await axios.get('/api/telegram-notify/config');
                const data = res.data;
                telegramNotifyConfig.enabled = data.enabled || false;
                telegramNotifyConfig.name = data.name || 'Telegram';
                telegramNotifyConfig.bot_token = data.bot_token || '';
                telegramNotifyConfig.chat_id = data.chat_id || '';
                if (data.notify_types) {
                    telegramNotifyConfig.notify_types = { ...telegramNotifyConfig.notify_types, ...data.notify_types };
                }
                // 加载模板
                if (data.templates) {
                    for (const key of Object.keys(defaultTemplates)) {
                        if (data.templates[key]) {
                            telegramNotifyConfig.templates[key] = { ...defaultTemplates[key], ...data.templates[key] };
                        }
                    }
                }
            } catch(e) {
                console.error('获取Telegram通知配置失败', e);
            }
        };

        const toggleTelegramNotifyType = (typeKey) => {
            if (telegramNotifyConfig.notify_types) {
                telegramNotifyConfig.notify_types[typeKey] = !telegramNotifyConfig.notify_types[typeKey];
            }
        };

        const saveTelegramNotifyConfig = async () => {
            telegramNotifySaving.value = true;
            try {
                const payload = {
                    enabled: telegramNotifyConfig.enabled,
                    name: telegramNotifyConfig.name,
                    bot_token: telegramNotifyConfig.bot_token,
                    chat_id: telegramNotifyConfig.chat_id,
                    notify_types: telegramNotifyConfig.notify_types,
                    templates: sanitizeTemplates(telegramNotifyConfig.templates)
                };
                await axios.post('/api/telegram-notify/config', payload);
                showToast('Telegram通知配置已保存', 'success');
            } catch(e) {
                showToast('保存失败: ' + (e.response?.data?.detail || e.message), 'error');
            } finally {
                telegramNotifySaving.value = false;
            }
        };

        const testTelegramNotify = async () => {
            const ok = await confirmNotificationAction('Telegram', '测试连接');
            if (!ok) return;
            telegramNotifyTesting.value = true;
            try {
                const res = await axios.post('/api/telegram-notify/test');
                if (res.data.status === 'ok') {
                    showToast('连接成功: ' + res.data.message, 'success');
                } else {
                    showToast('连接失败: ' + res.data.message, 'error');
                }
            } catch(e) {
                showToast('测试失败: ' + (e.response?.data?.detail || e.message), 'error');
            } finally {
                telegramNotifyTesting.value = false;
            }
        };

        const sendTelegramTestMsg = async () => {
            const ok = await confirmNotificationAction('Telegram', '发送测试消息');
            if (!ok) return;
            telegramNotifySending.value = true;
            try {
                const res = await axios.post('/api/telegram-notify/send?message=这是一条来自ALSemby的测试消息');
                if (res.data.status === 'ok') {
                    showToast('测试消息发送成功', 'success');
                } else {
                    showToast('发送失败: ' + res.data.message, 'error');
                }
            } catch(e) {
                showToast('发送失败: ' + (e.response?.data?.detail || e.message), 'error');
            } finally {
                telegramNotifySending.value = false;
            }
        };

        const telegramTemplateTesting = ref(false);
        const testTelegramTemplate = async () => {
            const ok = await confirmNotificationAction('Telegram', '发送模板测试通知');
            if (!ok) return;
            telegramTemplateTesting.value = true;
            try {
                // 先保存配置确保模板已持久化
                const payload = {
                    enabled: telegramNotifyConfig.enabled,
                    name: telegramNotifyConfig.name,
                    bot_token: telegramNotifyConfig.bot_token,
                    chat_id: telegramNotifyConfig.chat_id,
                    notify_types: telegramNotifyConfig.notify_types,
                    templates: sanitizeTemplates(telegramNotifyConfig.templates)
                };
                await axios.post('/api/telegram-notify/config', payload);
                const res = await axios.post('/api/telegram-notify/test-template');
                if (res.data.status === 'ok') {
                    showToast('模板测试通知发送成功', 'success');
                } else {
                    showToast('模板测试失败: ' + res.data.message, 'error');
                }
            } catch(e) {
                showToast('模板测试失败: ' + (e.response?.data?.detail || e.message), 'error');
            } finally {
                telegramTemplateTesting.value = false;
            }
        };

        // 模板辅助函数
        const sanitizeTemplates = (templates) => {
            const result = {};
            for (const [key, tpl] of Object.entries(templates)) {
                result[key] = { title: tpl.title || '', text: tpl.text || '' };
            }
            return result;
        };

        const resetWechatTemplate = (tplKey) => {
            if (defaultTemplates[tplKey]) {
                wechatNotifyConfig.templates[tplKey] = JSON.parse(JSON.stringify(defaultTemplates[tplKey]));
            }
        };

        const resetTelegramTemplate = (tplKey) => {
            if (defaultTemplates[tplKey]) {
                telegramNotifyConfig.templates[tplKey] = JSON.parse(JSON.stringify(defaultTemplates[tplKey]));
            }
        };

        const wrapVar = (v) => '{{ ' + v + ' }}';

        const updateAccount = async () => { 
            if(!accountForm.old_password || !accountForm.new_password) return showToast("请填写密码", 'error'); 
            updatingAccount.value = true; 
            try { 
                await axios.post('/api/change_auth', accountForm); 
                showToast("修改成功，请重新登录", 'success'); 
                localStorage.setItem('username', accountForm.new_username); 
                currentUsername.value = accountForm.new_username; 
                setTimeout(logout, 1500); 
            } catch (e) { showToast("修改失败", 'error'); } finally { updatingAccount.value = false; } 
        };
        
        watch(fontList, (newList) => { const old = document.getElementById('dynamic-font-styles'); if (old) old.remove(); let css = ''; newList.forEach(f => { css += `@font-face { font-family: '${f}'; src: url('/fonts/${f}'); font-display: swap; }`; }); const s = document.createElement('style'); s.id = 'dynamic-font-styles'; s.textContent = css; document.head.appendChild(s); }, { immediate: true, deep: true });
        watch(uiMode, (mode) => {
            if (designerBackgroundCustomized.value || designerElements.value.length || currentDesignerPresetFile.value) return;
            designerBgColor.value = defaultDesignerBgColor(mode);
            resetDesignerHistory();
        });

        return {
            tab, pageTitle, servers, fontList, presetList, layoutGroups, orderedLayoutGroups, config, creationMode,
            uiMode, commandOpen, commandQuery, commandInput, settingsOpen, creationOpen, filteredCommandItems, setUiMode, runCommand, openSetting, openCreation,
            manualServerIdx, currentManualServer, currentLibId, previewImage, loading, applying, selectedPresetIdx, currentPresetFile,
            previewServerIdx, libraryCards, loadingCovers, suiteList, newSuiteName, creatingBackup, viewingSuite, viewingSuiteImages, selectedRestoreIds,
            taskName, taskCron, taskEngine, taskPreset, runningTask, runTaskNow, createTask, taskList, deleteTask, selectedAutoTargetCount,
            translationList, fetchTranslations, saveTranslations, addTransRow, removeTransRow, 
            fetchLibraryCovers, createSuiteBackup, deleteSuite, viewSuite, closeSuiteView, getLibraryName, toggleRestoreSelect, restoreSelected, restoreAll,
            addServer, removeServer, testConnection, saveAllConfigs, onServerUserNameChange, fetchLibs, onManualServerChange, onLibChange, preview, apply, saveAsNewPreset, overwritePreset, loadPreset, deleteTemplate, toggleServerExpand, isLibSelected, toggleLibSelection, uploadFont, deleteFont, logout,
            designerCanvas, designerElements, selectedDesignerId, selectedDesignerElement, designerTextEditingId, designerBgColor, designerGrid, designerSnap, designerStage,
            designerTemplateName, selectedDesignerPreset, currentDesignerPresetFile, designerPresets, designerHistory, designerHistoryIndex,
            designerTypeMeta, designerElementLabel, designerElementStyle, designerTextPaintStyle, designerTextPreview, addDesignerElement, removeDesignerElement,
            designerLayerDragId, designerLayerDropId, designerLayerDropEdge, startDesignerLayerReorder,
            duplicateDesignerElement, moveDesignerLayer, toggleDesignerLayer, startDesignerPointer, startDesignerTextEdit, finishDesignerTextEdit, newDesignerTemplate, loadDesignerPreset,
            saveDesignerTemplate, commitDesignerHistory, updateDesignerBackground, undoDesigner, redoDesigner,
            gradientPresets, applyGradientPreset, applyDesignerGradientPreset,
            selectedTemplates, templatePreviewVersion, templateImportInput, toggleTemplateSelection, exportTemplate, exportTemplateBatch, importTemplates,
            coverAssets, materialModalVisible, materialModalTitle, materialModalType, materialModalSource, materialModalStep,
            materialModalImages, materialModalLoading, materialSearchQuery, materialSearchResults, openMaterialPicker, searchMaterial,
            fetchMaterialImages, toggleMaterialUrl, isMaterialSelected, closeMaterialModal, clearCoverAssets, handleBgUpload, handlePosterUpload,
            isAllSelected, toggleSelectAll, manualMode, taskMode, taskFallbackToNextBackdrop,
            layoutList, fetchLayouts, fetchLayoutAndPresets, filteredPresets, manualPresetOptions, userDesignerLayoutOptions, manualLayoutSelection, activeManualLayoutLabel,
            currentSchema, manualDesignerElements, manualDesignerBackdropElements, manualDesignerPosterElements,
            manualDesignerTextElements, manualDesignerShapeElements, manualDesignerElementLabel, setManualDesignerGroupValue,
            resizeDesignerPoster, setManualDesignerPosterSize,
            accountForm, updateAccount, updatingAccount,
            transServerIdx, loadTransFromLib, editingTaskId, editTask, cancelEdit, runSavedTask,
            tasksState, toggleTaskLog, accordions, toggleAccordion, showCreateTask, clearLogs,
            dashboardStats, wallRows, initDashboard,
            toasts, showToast,
            confirmState, handleConfirm,
            selectState, handleSelect, closeSelectDialog,
            projectVersion, currentUsername, stopTask,
            
            // [新增] 真实后台日志
            consoleLogState, openConsoleLog, closeConsoleLog, fetchSystemLogs, toggleConsoleAutoScroll,
            clearSystemLogs, setConsoleLogCategory, setConsoleLogLevel,

            // [新增] RSS 订阅
            rssForm, rssTasks,
            tmdbRankingOptions, tmdbSelectedOption, tmdbListLabel, tmdbListMedia,
            rssTaskSourceLabel, rssTaskTypeLabel, rssTaskTypeClass, rssTaskTypeIcon,
            createRssTask, runRssTask, deleteRssTask,

            // [新增] Webhook 
            webhookConfig, webhookUrl, fetchWebhookConfig, saveWebhookConfig, toggleWebhookCoverStatus, copyWebhookUrl,
            webhookDebugState, fetchWebhookDebug, fillWebhookPayloadExample, parseWebhookPayload,

            // [新增] 工具系统总览
            toolsState, fetchToolsSummary, toolStatusMeta, openToolCard,

            // [新增] 诊断助手
            diagnosticsState, fetchDiagnosticsSummary, runReadonlyEmbyCheck,
            logCenterState, logCategoryOptions, logLevelOptions, logTimeOptions, fetchLogCenter, toggleLogEntryDetail,
            configAssistantState, fetchConfigAssistant, configStatusMeta, jumpToConfigTarget,
            mediaToolsState, mediaIssueOptions, mediaTypeOptions, fetchMediaToolsLibraries, runMediaMaintenanceSearch,
            formatMediaSize, mediaTypeLabel, mediaIssueSeverity, mediaSeverityMeta, mediaItemSeverity,
            mediaIssueBlueprint, mediaResultAdvice, copyMediaPath, openEmbyItem, exportMediaMaintenanceCsv, refreshMediaMetadata,
            embyTasksState, fetchEmbyTasksLibraries, fetchEmbyScheduledTasks,
            embyTaskStateLabel, embyTaskLastResult, embyTaskGroups, embyTaskCategoryFilters,
            embyTaskResultFilters, embyTaskRunningCount, embyTaskFailedCount, embyTaskVisibleCount,
            embyTaskShenyiCount, embyTaskCategoryLabel, embyTaskGroupIcon,
            embyTaskGroupDescription, embyTaskBlueprint, embyTaskLastResultStatusLabel, embyTaskResultTone, embyTaskResultIcon,
            openEmbyTaskLogs,
            runEmbyScheduledTask, stopEmbyScheduledTask,
            collectionsState, collectionIssueOptions, collectionIssueBlueprint, collectionResultAdvice, fetchCollectionLibraries, fetchCollectionSummary,
            fetchCollectionItems, refreshCollectionMetadata, collectionItemSeverity, exportCollectionCsv,

            bgUploadInput, posterUploadInput, fontUploadInput, triggerFileInput,

            // [新增] 微信通知配置
            wechatNotifyConfig, wechatNotifyTesting, wechatNotifySending, wechatNotifySaving, wechatTemplateTesting,
            fetchWechatNotifyConfig, saveWechatNotifyConfig, testWechatNotify, sendWechatTestMsg, testWechatTemplate,
            notificationTypes, toggleNotifyType, templateVars, resetWechatTemplate, resetTelegramTemplate, wrapVar,

            // [新增] Telegram通知配置
            telegramNotifyConfig, telegramNotifyTesting, telegramNotifySending, telegramNotifySaving, telegramTemplateTesting,
            fetchTelegramNotifyConfig, saveTelegramNotifyConfig, testTelegramNotify, sendTelegramTestMsg, testTelegramTemplate,
            toggleTelegramNotifyType,
            
            bottomMenu, isCoverTab, isCreationTab, isAutomationTab, isSettingsTab, layoutLabel, webhookPresetLabel, selectBottomTab, toggleBottomMenu,
            editingRssTaskId, editRssTask, cancelRssEdit,
            
            // 新增开关控制方法
            toggleTaskStatus,
            toggleRssStatus,
            callbackUrl,
        }
        
    }
}).mount('#app')
