// ============================================================
//  ZINTOO AI — Frontend Application
//  Full API integration with graceful mock fallback
// ============================================================

// ── API SERVICE LAYER ─────────────────────────────────────────
const API_BASE = 'http://localhost:8000';

const ApiService = {
    online: false,

    async request(method, path, body = null) {
        const opts = {
            method,
            headers: { 'Content-Type': 'application/json' },
        };
        if (body) opts.body = JSON.stringify(body);
        const resp = await fetch(`${API_BASE}${path}`, opts);
        if (!resp.ok) throw new Error(`API ${resp.status}`);
        return resp.json();
    },

    async checkHealth() {
        try {
            const d = await this.request('GET', '/health');
            this.online = d.status === 'healthy';
        } catch { this.online = false; }
        return this.online;
    },

    // Products
    async getProducts(category = null, limit = 50) {
        const q = category ? `?category=${category}&limit=${limit}` : `?limit=${limit}`;
        return this.request('GET', `/api/products${q}`);
    },

    async getProduct(id) {
        return this.request('GET', `/api/products/${id}`);
    },

    // Recommendations (CLIP multimodal)
    async getRecommendations(textInput, pincode = '110001', topK = 10) {
        return this.request('POST', '/api/recommendations', {
            text_input: textInput,
            pincode: pincode,
            top_k: topK,
        });
    },

    // Forecasts
    async getForecasts(sku, pincode, limit = 48) {
        return this.request('GET', `/api/forecasts/${sku}/${pincode}?limit=${limit}`);
    },

    // Inventory
    async getInventoryByPincode(pincode) {
        return this.request('GET', `/api/inventory/pincode/${pincode}`);
    },
    async checkStock(sku, pincode) {
        return this.request('GET', `/api/inventory/stock/${sku}/${pincode}`);
    },

    // Orders
    async getOrdersByStatus(status, limit = 50) {
        return this.request('GET', `/api/orders/status/${status}?limit=${limit}`);
    },

    // Agent
    async triggerOptimization(pincode) {
        return this.request('POST', `/api/agent/trigger-optimization?pincode=${pincode}`);
    },
    async getAgentLogs(limit = 50) {
        return this.request('GET', `/api/agent-logs?limit=${limit}`);
    },
    async getReallocations(limit = 50) {
        return this.request('GET', `/api/reallocations?limit=${limit}`);
    },

    // SLA / Stats
    async getSLAMetrics() {
        return this.request('GET', '/api/stats/sla');
    },
};

const App = {
    currentPage: 'dashboard',
    charts: {},
    agentInterval: null,
    notifications: [],

    // ── MOCK DATA ──────────────────────────────────────────────
    products: [
        // ─── Kurtas ───
        { id: 'P001', name: 'Indigo Cotton Kurta', sku: 'KURTA_001_M_BLU', category: 'Kurtas', price: 1299, rating: 4.5, stock: 48, color: 'Blue', size: 'M', img: 'https://images.unsplash.com/photo-1614252235316-8c857d38b5f4?w=400&h=500&fit=crop' },
        { id: 'P002', name: 'Sky Blue Linen Tunic', sku: 'TUNIC_002_L_BLU', category: 'Kurtas', price: 1599, rating: 4.2, stock: 23, color: 'Blue', size: 'L', img: 'https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=400&h=500&fit=crop' },
        { id: 'P003', name: 'Navy Casual Kurta', sku: 'KURTA_003_M_NVY', category: 'Kurtas', price: 2199, rating: 4.7, stock: 12, color: 'Navy', size: 'M', img: 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400&h=500&fit=crop' },
        { id: 'P011', name: 'Printed Ethnic Kurta', sku: 'KURTA_009_M_MRN', category: 'Kurtas', price: 1799, rating: 4.0, stock: 42, color: 'Maroon', size: 'M', img: 'https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=400&h=500&fit=crop' },
        { id: 'P025', name: 'Embroidered Silk Kurta', sku: 'KURTA_025_L_GLD', category: 'Kurtas', price: 3499, rating: 4.8, stock: 9, color: 'Gold', size: 'L', img: 'https://images.unsplash.com/photo-1617137968427-85924c800a22?w=400&h=500&fit=crop' },

        // ─── Shirts ───
        { id: 'P004', name: 'Classic White Shirt', sku: 'SHIRT_002_L_WHT', category: 'Shirts', price: 1899, rating: 4.3, stock: 67, color: 'White', size: 'L', img: 'https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=400&h=500&fit=crop' },
        { id: 'P013', name: 'Blue Oxford Shirt', sku: 'SHIRT_013_M_BLU', category: 'Shirts', price: 2199, rating: 4.4, stock: 38, color: 'Blue', size: 'M', img: 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400&h=500&fit=crop' },
        { id: 'P014', name: 'Casual Linen Shirt', sku: 'SHIRT_014_L_BEG', category: 'Shirts', price: 1699, rating: 4.1, stock: 55, color: 'Beige', size: 'L', img: 'https://images.unsplash.com/photo-1607345366928-199ea26cfe3e?w=400&h=500&fit=crop' },
        { id: 'P026', name: 'Formal Black Shirt', sku: 'SHIRT_026_M_BLK', category: 'Shirts', price: 2399, rating: 4.5, stock: 29, color: 'Black', size: 'M', img: 'https://images.unsplash.com/photo-1620012253295-c15cc3e65df4?w=400&h=500&fit=crop' },
        { id: 'P027', name: 'Striped Cotton Shirt', sku: 'SHIRT_027_L_STR', category: 'Shirts', price: 1999, rating: 4.2, stock: 44, color: 'Stripe', size: 'L', img: 'https://images.unsplash.com/photo-1598033129183-c4f50c736c10?w=400&h=500&fit=crop' },

        // ─── Jeans & Pants ───
        { id: 'P005', name: 'Slim Fit Black Jeans', sku: 'JEANS_003_M_BLK', category: 'Jeans', price: 2499, rating: 4.6, stock: 35, color: 'Black', size: 'M', img: 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=400&h=500&fit=crop' },
        { id: 'P015', name: 'Blue Denim Jeans', sku: 'JEANS_015_L_BLU', category: 'Jeans', price: 2299, rating: 4.3, stock: 52, color: 'Blue', size: 'L', img: 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=400&h=500&fit=crop' },
        { id: 'P028', name: 'Chino Khaki Pants', sku: 'PANT_028_M_KHK', category: 'Jeans', price: 1899, rating: 4.1, stock: 61, color: 'Khaki', size: 'M', img: 'https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=400&h=500&fit=crop' },

        // ─── Dresses ───
        { id: 'P006', name: 'Red Festive Dress', sku: 'DRESS_004_S_RED', category: 'Dresses', price: 3299, rating: 4.8, stock: 8, color: 'Red', size: 'S', img: 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400&h=500&fit=crop' },
        { id: 'P009', name: 'Floral Summer Dress', sku: 'DRESS_007_M_FLR', category: 'Dresses', price: 2799, rating: 4.1, stock: 31, color: 'Multicolor', size: 'M', img: 'https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=400&h=500&fit=crop' },
        { id: 'P016', name: 'Black Cocktail Dress', sku: 'DRESS_016_S_BLK', category: 'Dresses', price: 4599, rating: 4.7, stock: 6, color: 'Black', size: 'S', img: 'https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=400&h=500&fit=crop' },
        { id: 'P029', name: 'White Maxi Dress', sku: 'DRESS_029_M_WHT', category: 'Dresses', price: 3199, rating: 4.4, stock: 18, color: 'White', size: 'M', img: 'https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?w=400&h=500&fit=crop' },
        { id: 'P030', name: 'Yellow Sundress', sku: 'DRESS_030_S_YLW', category: 'Dresses', price: 2499, rating: 4.3, stock: 22, color: 'Yellow', size: 'S', img: 'https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=400&h=500&fit=crop' },

        // ─── Shoes ───
        { id: 'P007', name: 'Leather Casual Sneakers', sku: 'SHOE_005_9_BRN', category: 'Shoes', price: 3999, rating: 4.4, stock: 19, color: 'Brown', size: '9', img: 'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400&h=500&fit=crop' },
        { id: 'P012', name: 'Running Sports Shoes', sku: 'SHOE_010_10_GRY', category: 'Shoes', price: 2999, rating: 4.5, stock: 27, color: 'Grey', size: '10', img: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=500&fit=crop' },
        { id: 'P017', name: 'White Canvas Sneakers', sku: 'SHOE_017_8_WHT', category: 'Shoes', price: 2499, rating: 4.6, stock: 33, color: 'White', size: '8', img: 'https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?w=400&h=500&fit=crop' },
        { id: 'P018', name: 'Formal Oxford Shoes', sku: 'SHOE_018_9_BLK', category: 'Shoes', price: 5999, rating: 4.8, stock: 11, color: 'Black', size: '9', img: 'https://images.unsplash.com/photo-1614252369475-531eba835eb1?w=400&h=500&fit=crop' },
        { id: 'P031', name: 'High Top Sneakers', sku: 'SHOE_031_10_RED', category: 'Shoes', price: 4499, rating: 4.3, stock: 15, color: 'Red', size: '10', img: 'https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=400&h=500&fit=crop' },
        { id: 'P032', name: 'Suede Loafers', sku: 'SHOE_032_9_TAN', category: 'Shoes', price: 3499, rating: 4.5, stock: 20, color: 'Tan', size: '9', img: 'https://images.unsplash.com/photo-1533867617858-e7b97e060509?w=400&h=500&fit=crop' },

        // ─── Accessories ───
        { id: 'P008', name: 'Designer Leather Handbag', sku: 'BAG_006_OS_BLK', category: 'Accessories', price: 5499, rating: 4.9, stock: 5, color: 'Black', size: 'OS', img: 'https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=400&h=500&fit=crop' },
        { id: 'P019', name: 'Aviator Sunglasses', sku: 'ACC_019_OS_GLD', category: 'Accessories', price: 1999, rating: 4.3, stock: 45, color: 'Gold', size: 'OS', img: 'https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400&h=500&fit=crop' },
        { id: 'P020', name: 'Leather Belt', sku: 'ACC_020_M_BRN', category: 'Accessories', price: 999, rating: 4.1, stock: 78, color: 'Brown', size: 'M', img: 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=500&fit=crop' },
        { id: 'P033', name: 'Canvas Tote Bag', sku: 'BAG_033_OS_NAT', category: 'Accessories', price: 1299, rating: 4.2, stock: 36, color: 'Natural', size: 'OS', img: 'https://images.unsplash.com/photo-1544816155-12df9643f363?w=400&h=500&fit=crop' },
        { id: 'P034', name: 'Silk Scarf', sku: 'ACC_034_OS_MUL', category: 'Accessories', price: 1599, rating: 4.6, stock: 28, color: 'Multicolor', size: 'OS', img: 'https://images.unsplash.com/photo-1601924921557-45e6dea0e2ff?w=400&h=500&fit=crop' },

        // ─── Jackets & Outerwear ───
        { id: 'P010', name: 'Warm Puffer Jacket', sku: 'JACK_008_L_GRN', category: 'Jackets', price: 4999, rating: 4.6, stock: 14, color: 'Green', size: 'L', img: 'https://images.unsplash.com/photo-1544923246-77307dd270cb?w=400&h=500&fit=crop' },
        { id: 'P021', name: 'Denim Jacket', sku: 'JACK_021_M_BLU', category: 'Jackets', price: 3499, rating: 4.5, stock: 21, color: 'Blue', size: 'M', img: 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400&h=500&fit=crop' },
        { id: 'P022', name: 'Black Leather Jacket', sku: 'JACK_022_L_BLK', category: 'Jackets', price: 7999, rating: 4.9, stock: 4, color: 'Black', size: 'L', img: 'https://images.unsplash.com/photo-1521223890158-f9f7c3d5d504?w=400&h=500&fit=crop' },
        { id: 'P035', name: 'Bomber Jacket', sku: 'JACK_035_M_OLV', category: 'Jackets', price: 4299, rating: 4.4, stock: 16, color: 'Olive', size: 'M', img: 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=400&h=500&fit=crop' },

        // ─── Ethnic / Sarees ───
        { id: 'P023', name: 'Banarasi Silk Saree', sku: 'SAREE_023_OS_RED', category: 'Sarees', price: 8999, rating: 4.9, stock: 7, color: 'Red', size: 'OS', img: 'https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=400&h=500&fit=crop&q=80' },
        { id: 'P024', name: 'Chiffon Party Saree', sku: 'SAREE_024_OS_PNK', category: 'Sarees', price: 4599, rating: 4.5, stock: 13, color: 'Pink', size: 'OS', img: 'https://images.unsplash.com/photo-1583391733956-6c78276477e2?w=400&h=500&fit=crop' },
        { id: 'P036', name: 'Cotton Handloom Saree', sku: 'SAREE_036_OS_BLU', category: 'Sarees', price: 3299, rating: 4.3, stock: 25, color: 'Blue', size: 'OS', img: 'https://images.unsplash.com/photo-1614252235316-8c857d38b5f4?w=400&h=500&fit=crop&q=80' },
    ],

    orders: [
        { id: 'ORD-7841', customer: 'Priya Sharma', items: 3, total: 5097, pincode: '110001', status: 'delivered', date: '2026-03-28' },
        { id: 'ORD-7842', customer: 'Rahul Gupta', items: 1, total: 2499, pincode: '400001', status: 'processing', date: '2026-03-28' },
        { id: 'ORD-7843', customer: 'Anita Desai', items: 2, total: 8298, pincode: '560001', status: 'pending', date: '2026-03-27' },
        { id: 'ORD-7844', customer: 'Vikram Singh', items: 1, total: 3999, pincode: '700001', status: 'transit', date: '2026-03-27' },
        { id: 'ORD-7845', customer: 'Meera Patel', items: 4, total: 9596, pincode: '110001', status: 'delivered', date: '2026-03-26' },
        { id: 'ORD-7846', customer: 'Arjun Nair', items: 2, total: 4298, pincode: '560001', status: 'cancelled', date: '2026-03-26' },
        { id: 'ORD-7847', customer: 'Kavita Rao', items: 1, total: 1299, pincode: '400001', status: 'delivered', date: '2026-03-25' },
        { id: 'ORD-7848', customer: 'Deepak Kumar', items: 3, total: 7497, pincode: '110001', status: 'processing', date: '2026-03-25' },
    ],

    stockEntries: [
        { sku: 'KURTA_001_M_BLU', warehouse: 'WH-Delhi-A', pincode: '110001', qty: 48, status: 'in-stock' },
        { sku: 'KURTA_001_M_BLU', warehouse: 'WH-Mumbai-B', pincode: '400001', qty: 5, status: 'in-stock' },
        { sku: 'SHIRT_002_L_WHT', warehouse: 'WH-Delhi-A', pincode: '110001', qty: 67, status: 'in-stock' },
        { sku: 'JEANS_003_M_BLK', warehouse: 'WH-Bangalore-C', pincode: '560001', qty: 35, status: 'in-stock' },
        { sku: 'DRESS_004_S_RED', warehouse: 'WH-Delhi-A', pincode: '110001', qty: 3, status: 'in-stock' },
        { sku: 'DRESS_004_S_RED', warehouse: 'WH-Kolkata-D', pincode: '700001', qty: 0, status: 'out-of-stock' },
        { sku: 'SHOE_005_9_BRN', warehouse: 'WH-Mumbai-B', pincode: '400001', qty: 19, status: 'in-stock' },
        { sku: 'BAG_006_OS_BLK', warehouse: 'WH-Delhi-A', pincode: '110001', qty: 5, status: 'in-stock' },
        { sku: 'SHOE_010_10_GRY', warehouse: 'WH-Bangalore-C', pincode: '560001', qty: 0, status: 'out-of-stock' },
    ],

    reallocations: [
        { id: 'RA-301', sku: 'KURTA_001_M_BLU', from: 'WH-Mumbai-B', to: 'WH-Delhi-A', qty: 40, status: 'completed', time: '10:32 AM' },
        { id: 'RA-302', sku: 'DRESS_004_S_RED', from: 'WH-Delhi-A', to: 'WH-Kolkata-D', qty: 15, status: 'transit', time: '10:45 AM' },
        { id: 'RA-303', sku: 'SHOE_010_10_GRY', from: 'WH-Mumbai-B', to: 'WH-Bangalore-C', qty: 25, status: 'pending', time: '11:02 AM' },
        { id: 'RA-304', sku: 'JEANS_003_M_BLK', from: 'WH-Delhi-A', to: 'WH-Mumbai-B', qty: 30, status: 'completed', time: '11:15 AM' },
        { id: 'RA-305', sku: 'SHIRT_002_L_WHT', from: 'WH-Kolkata-D', to: 'WH-Delhi-A', qty: 50, status: 'completed', time: '11:28 AM' },
    ],

    agentLogs: [
        { type: 'info', msg: 'Pulse check: Gathering regional deficit data...' },
        { type: 'info', msg: 'Analyzing pincode <strong>110001</strong> demand patterns' },
        { type: 'action', msg: 'Demand spike predicted for SKU_402 — Festive Season trigger' },
        { type: 'action', msg: 'Locating idle inventory at Warehouse-C...' },
        { type: 'success', msg: 'Reallocated 140 units WH-C → WH-A. ETA 3hrs' },
        { type: 'info', msg: 'Verifying SLA coverage across 4 zones' },
        { type: 'success', msg: 'Optimization iteration complete. System nominal.' },
        { type: 'action', msg: 'Agent hibernating — next tick in 15m' },
        { type: 'warn', msg: 'Alert: Low stock KURTA_001_M_BLU in North region' },
        { type: 'info', msg: 'Priority override: Waking agent for region South' },
        { type: 'action', msg: 'Running multi-zone demand comparison...' },
        { type: 'success', msg: 'Fulfilled 23 pending orders via nearest warehouse routing' },
    ],

    // ── INITIALIZATION ────────────────────────────────────────
    async init() {
        lucide.createIcons();
        this.initNavigation();
        this.initTopbar();
        this.initNotifications();
        this.initDiscovery();
        this.initForecasts();
        this.initInventory();
        this.initAgent();
        this.initSettings();
        this.startAgentFeed();

        // Check backend health & load live data
        const isOnline = await ApiService.checkHealth();
        this.updateConnectionStatus(isOnline);
        if (isOnline) {
            this.toast('Connected to Zintoo API backend', 'success');
            await this.loadLiveData();
        } else {
            this.toast('Backend offline — using demo data', 'info');
        }
        this.renderDashboard();

        // Poll health every 30s
        setInterval(async () => {
            const online = await ApiService.checkHealth();
            this.updateConnectionStatus(online);
        }, 30000);
    },

    updateConnectionStatus(online) {
        ApiService.online = online;
        const label = document.querySelector('.status-label');
        const sub = document.querySelector('.status-sub');
        const dot = document.querySelector('.sidebar-bottom .pulse-dot');
        if (label) label.textContent = online ? 'API Connected' : 'Demo Mode';
        if (sub) sub.textContent = online ? `Backend: ${API_BASE}` : 'Backend offline — mock data';
        if (dot) dot.style.background = online ? 'var(--green)' : 'var(--amber)';
    },

    async loadLiveData() {
        try {
            // Load products from API
            const productsResp = await ApiService.getProducts(null, 100);
            if (productsResp.products && productsResp.products.length > 0) {
                this.liveProducts = productsResp.products;
                document.getElementById('kpi-products').textContent = productsResp.total.toLocaleString();
            }
        } catch (e) { console.warn('Could not load products from API:', e); }

        try {
            const sla = await ApiService.getSLAMetrics();
            if (sla.total_orders > 0) {
                document.getElementById('kpi-demand').textContent = sla.total_orders.toLocaleString();
                document.getElementById('kpi-realloc').textContent = sla.successful_deliveries?.toLocaleString() || '0';
                document.getElementById('kpi-ndcg').textContent = (sla.fulfilment_rate / 100).toFixed(2);
            }
        } catch (e) { console.warn('Could not load SLA metrics:', e); }
    },

    // ── NAVIGATION ────────────────────────────────────────────
    initNavigation() {
        document.querySelectorAll('.nav-link[data-page]').forEach(link => {
            link.addEventListener('click', e => {
                e.preventDefault();
                this.navigateTo(link.dataset.page);
            });
        });
    },

    navigateTo(page) {
        // Update nav
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        const activeLink = document.querySelector(`.nav-link[data-page="${page}"]`);
        if (activeLink) activeLink.classList.add('active');

        // Update pages
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        const target = document.getElementById(`page-${page}`);
        if (target) {
            target.classList.add('active');
            target.scrollTop = 0;
        }

        // Close mobile sidebar
        document.getElementById('sidebar').classList.remove('open');

        this.currentPage = page;

        // Lazy init charts
        if (page === 'forecasts' && !this.charts.forecast) this.renderForecastChart();
        if (page === 'dashboard' && !this.charts.dash) this.renderDashChart();
    },

    // ── TOPBAR ────────────────────────────────────────────────
    initTopbar() {
        // Hamburger
        document.getElementById('hamburger-btn').addEventListener('click', () => {
            document.getElementById('sidebar').classList.toggle('open');
        });

        // Theme toggle
        document.getElementById('theme-toggle').addEventListener('click', () => {
            this.toast('Theme toggle — light mode coming soon!', 'info');
        });

        // Notifications
        document.getElementById('notif-btn').addEventListener('click', () => {
            document.getElementById('notif-panel').classList.toggle('open');
        });

        // Close notif panel when clicking outside
        document.addEventListener('click', e => {
            const panel = document.getElementById('notif-panel');
            const btn = document.getElementById('notif-btn');
            if (panel.classList.contains('open') && !panel.contains(e.target) && !btn.contains(e.target)) {
                panel.classList.remove('open');
            }
        });

        document.getElementById('clear-notifs').addEventListener('click', () => {
            this.notifications = [];
            this.renderNotifications();
            document.querySelector('.notif-count').style.display = 'none';
            this.toast('Notifications cleared', 'success');
        });

        // Profile
        document.getElementById('profile-btn').addEventListener('click', () => {
            this.toast('Profile settings panel — coming soon!', 'info');
        });

        // Global search
        document.getElementById('global-search').addEventListener('keypress', e => {
            if (e.key === 'Enter') {
                const q = e.target.value.trim();
                if (q) {
                    this.navigateTo('discovery');
                    document.getElementById('discovery-input').value = q;
                    setTimeout(() => this.doDiscoverySearch(q), 200);
                }
            }
        });

        // Export
        document.getElementById('export-btn')?.addEventListener('click', () => {
            this.toast('Report exported to downloads/', 'success');
        });

        // Optimize Now
        document.getElementById('optimize-btn')?.addEventListener('click', () => {
            this.toast('Triggering global orchestration optimization...', 'info');
            setTimeout(() => this.toast('Optimization complete ✓ — 12 reallocations made', 'success'), 2000);
        });
    },

    // ── NOTIFICATIONS ─────────────────────────────────────────
    initNotifications() {
        this.notifications = [
            { title: 'Low Stock Alert', desc: 'DRESS_004_S_RED has only 3 units left in WH-Delhi-A', time: '5 min ago' },
            { title: 'Reallocation Complete', desc: '140 units of KURTA_001 moved from WH-C to WH-A', time: '12 min ago' },
            { title: 'Agent Optimization', desc: 'Auto-optimization cycle completed. 97% SLA maintained.', time: '28 min ago' },
        ];
        this.renderNotifications();
    },

    renderNotifications() {
        const list = document.getElementById('notif-list');
        if (this.notifications.length === 0) {
            list.innerHTML = '<p style="text-align:center;color:var(--text-muted);padding:40px;">No notifications</p>';
            return;
        }
        list.innerHTML = this.notifications.map(n => `
            <div class="notif-item">
                <div class="notif-item-title">${n.title}</div>
                <div class="notif-item-desc">${n.desc}</div>
                <div class="notif-item-time">${n.time}</div>
            </div>
        `).join('');
    },

    // ── DASHBOARD ─────────────────────────────────────────────
    renderDashboard() {
        this.renderDashChart();
        this.renderRecentOrders();
    },

    renderDashChart() {
        const ctx = document.getElementById('dashChart');
        if (!ctx) return;
        if (this.charts.dash) this.charts.dash.destroy();

        const labels = [];
        const now = new Date();
        for (let i = -24; i <= 24; i++) {
            const t = new Date(now.getTime() + i * 3600000);
            labels.push(t.getHours().toString().padStart(2, '0') + ':00');
        }

        const data = labels.map((_, i) => {
            const x = i - 24;
            return Math.max(8, Math.round(420 * Math.exp(-(x * x) / 80) + (Math.random() - 0.5) * 50));
        });

        this.charts.dash = new Chart(ctx, {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: 'Demand',
                    data,
                    borderColor: '#22d3ee',
                    backgroundColor: 'rgba(34,211,238,0.08)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2.5,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                }]
            },
            options: this.chartOptions()
        });
    },

    renderRecentOrders() {
        const tbody = document.querySelector('#recent-orders-table tbody');
        tbody.innerHTML = this.orders.slice(0, 5).map(o => `
            <tr>
                <td><strong>${o.id}</strong></td>
                <td>${o.customer}</td>
                <td>${o.items}</td>
                <td>₹${o.total.toLocaleString()}</td>
                <td><span class="status-badge ${o.status}">${o.status}</span></td>
                <td><button class="btn btn-ghost btn-sm" onclick="App.viewOrder('${o.id}')">View</button></td>
            </tr>
        `).join('');
    },

    viewOrder(id) {
        const o = this.orders.find(x => x.id === id);
        if (!o) return;
        this.openModal(`
            <h2 style="margin-bottom:16px;">${o.id}</h2>
            <div class="modal-detail-row"><span class="modal-detail-label">Customer</span><span class="modal-detail-value">${o.customer}</span></div>
            <div class="modal-detail-row"><span class="modal-detail-label">Items</span><span class="modal-detail-value">${o.items}</span></div>
            <div class="modal-detail-row"><span class="modal-detail-label">Total</span><span class="modal-detail-value">₹${o.total.toLocaleString()}</span></div>
            <div class="modal-detail-row"><span class="modal-detail-label">Pincode</span><span class="modal-detail-value">${o.pincode}</span></div>
            <div class="modal-detail-row"><span class="modal-detail-label">Status</span><span class="modal-detail-value"><span class="status-badge ${o.status}">${o.status}</span></span></div>
            <div class="modal-detail-row"><span class="modal-detail-label">Date</span><span class="modal-detail-value">${o.date}</span></div>
        `);
    },

    // ── AI DISCOVERY ──────────────────────────────────────────
    initDiscovery() {
        document.getElementById('discovery-search-btn').addEventListener('click', () => {
            const q = document.getElementById('discovery-input').value.trim();
            if (q) this.doDiscoverySearch(q);
        });

        document.getElementById('discovery-input').addEventListener('keypress', e => {
            if (e.key === 'Enter') {
                const q = e.target.value.trim();
                if (q) this.doDiscoverySearch(q);
            }
        });

        // Quick tags
        document.querySelectorAll('.tag[data-query]').forEach(tag => {
            tag.addEventListener('click', () => {
                document.getElementById('discovery-input').value = tag.dataset.query;
                this.doDiscoverySearch(tag.dataset.query);
            });
        });

        document.getElementById('upload-img-btn').addEventListener('click', () => {
            this.toast('Image upload — CLIP model integration coming soon!', 'info');
        });
    },

    async doDiscoverySearch(query) {
        const btn = document.getElementById('discovery-search-btn');
        const grid = document.getElementById('discovery-results');
        const meta = document.getElementById('discovery-meta');

        btn.disabled = true;
        btn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Searching...';
        grid.innerHTML = '<p style="color:var(--text-muted);padding:40px;text-align:center;">Searching with AI...</p>';
        lucide.createIcons();

        const startTime = performance.now();
        let results = [];
        let source = 'mock';

        // Try real API first
        if (ApiService.online) {
            try {
                const resp = await ApiService.getRecommendations(query, '110001', 12);
                if (resp.recommendations && resp.recommendations.length > 0) {
                    results = resp.recommendations.map(r => ({
                        id: r.product.product_id,
                        name: r.product.name,
                        sku: r.product.sku,
                        category: r.product.category,
                        price: r.product.price,
                        rating: r.product.rating || 4.0,
                        stock: r.availability_in_pincode || 0,
                        color: r.product.color,
                        size: r.product.size,
                        img: r.product.image_url || '',
                        score: r.similarity_score,
                    }));
                    source = 'api';
                }
            } catch (e) { console.warn('API recommendation failed, using fallback:', e); }
        }

        // Fallback to local fuzzy match
        if (results.length === 0) {
            const keywords = query.toLowerCase().split(/\s+/);
            results = this.products.map(p => {
                const text = `${p.name} ${p.category} ${p.color} ${p.sku}`.toLowerCase();
                let score = 0;
                keywords.forEach(kw => { if (text.includes(kw)) score += 0.25; });
                score = Math.min(0.99, score + Math.random() * 0.3 + 0.35);
                return { ...p, score: parseFloat(score.toFixed(2)) };
            });
            results.sort((a, b) => b.score - a.score);
            results = results.slice(0, 10);
        }

        const elapsed = ((performance.now() - startTime) / 1000).toFixed(2);
        meta.style.display = 'flex';
        document.getElementById('discovery-count').textContent = `${results.length} results${source === 'api' ? ' (AI)' : ' (demo)'}`;
        document.getElementById('discovery-time').textContent = `${elapsed}s`;

        grid.innerHTML = results.map(p => {
            const matchClass = p.score >= 0.85 ? 'high' : p.score >= 0.7 ? 'mid' : 'low';
            const imgSrc = p.img && p.img.startsWith('http') ? p.img : '';
            const fallbackBg = `linear-gradient(135deg,hsl(${Math.random()*360},40%,25%),hsl(${Math.random()*360},50%,35%))`;
            return `
            <div class="product-card" onclick="App.viewProduct('${p.id}')">
                <div class="product-img">
                    ${imgSrc
                        ? `<img class="product-img-bg" src="${imgSrc}" alt="${p.name}" loading="lazy" onerror="this.style.display='none';this.parentElement.style.background='${fallbackBg}'">`
                        : `<div class="product-img-bg" style="background:${fallbackBg};width:100%;height:100%"></div>`
                    }
                    <div class="product-match ${matchClass}"><i data-lucide="zap"></i> ${Math.round(p.score * 100)}%</div>
                </div>
                <div class="product-body">
                    <div class="product-name">${p.name}</div>
                    <div class="product-row">
                        <span class="product-price">₹${Number(p.price).toLocaleString()}</span>
                        <span class="product-rating"><i data-lucide="star"></i> ${p.rating}</span>
                    </div>
                    <div class="product-stock">${p.stock > 0 ? `${p.stock} in stock` : 'Out of stock'}</div>
                </div>
            </div>`;
        }).join('');

        btn.disabled = false;
        btn.innerHTML = '<i data-lucide="sparkles"></i> Search';
        lucide.createIcons();
    },

    async viewProduct(id) {
        // Try to get from API first, fallback to local
        let p = this.products.find(x => x.id === id);
        if (ApiService.online) {
            try {
                const apiP = await ApiService.getProduct(id);
                if (apiP && apiP.name) {
                    p = { id: apiP.product_id, name: apiP.name, sku: apiP.sku, category: apiP.category, price: apiP.price, rating: apiP.rating, stock: 0, color: apiP.color, size: apiP.size, img: apiP.image_url || '' };
                }
            } catch(e) { /* use local */ }
        }
        if (!p) return;

        const imgSrc = p.img && p.img.startsWith('http') ? p.img : '';
        this.openModal(`
            <div class="modal-product-img">${imgSrc ? `<img src="${imgSrc}" alt="${p.name}" style="width:100%;height:100%;object-fit:cover;" onerror="this.style.display='none';this.parentElement.style.background='linear-gradient(135deg,#1e1e2a,#2a2a3a)'">` : `<div style="width:100%;height:100%;background:linear-gradient(135deg,#1e1e2a,#2a2a3a)"></div>`}</div>
            <div class="modal-product-title">${p.name}</div>
            <div class="modal-product-sku">SKU: ${p.sku}</div>
            <div class="modal-detail-row"><span class="modal-detail-label">Category</span><span class="modal-detail-value">${p.category}</span></div>
            <div class="modal-detail-row"><span class="modal-detail-label">Price</span><span class="modal-detail-value">₹${Number(p.price).toLocaleString()}</span></div>
            <div class="modal-detail-row"><span class="modal-detail-label">Color</span><span class="modal-detail-value">${p.color}</span></div>
            <div class="modal-detail-row"><span class="modal-detail-label">Size</span><span class="modal-detail-value">${p.size}</span></div>
            <div class="modal-detail-row"><span class="modal-detail-label">Rating</span><span class="modal-detail-value" style="color:var(--amber);">★ ${p.rating}</span></div>
            <div class="modal-detail-row"><span class="modal-detail-label">Stock</span><span class="modal-detail-value"><span class="status-badge ${p.stock > 0 ? 'in-stock' : 'out-of-stock'}">${p.stock > 0 ? p.stock + ' available' : 'Out of stock'}</span></span></div>
            <div class="modal-detail-row"><span class="modal-detail-label">Source</span><span class="modal-detail-value"><span class="status-badge ${ApiService.online ? 'in-stock' : 'pending'}">${ApiService.online ? '🟢 Live API' : '🟡 Demo'}</span></span></div>
            <div class="modal-actions">
                <button class="btn btn-primary" onclick="App.checkStockAction('${p.sku}')"><i data-lucide="sparkles"></i> Check Availability</button>
                <button class="btn btn-outline" onclick="App.toast('Added to recommendation pipeline','success')"><i data-lucide="package"></i> Recommend</button>
            </div>
        `);
        lucide.createIcons();
    },

    async checkStockAction(sku) {
        if (ApiService.online) {
            try {
                const resp = await ApiService.checkStock(sku, '110001');
                this.toast(`${sku} in 110001: ${resp.available_stock} units (${resp.can_fulfill ? 'Can fulfill ✓' : 'Cannot fulfill ✗'})`, resp.can_fulfill ? 'success' : 'error');
                return;
            } catch(e) {}
        }
        this.toast(`Stock check (demo): ${Math.floor(Math.random() * 50)} units available`, 'info');
    },

    // ── FORECASTS ─────────────────────────────────────────────
    initForecasts() {
        document.getElementById('fc-run-btn').addEventListener('click', () => this.renderForecastChart());
        this.renderForecastChart();
    },

    async renderForecastChart() {
        const ctx = document.getElementById('forecastChart');
        if (!ctx) return;
        if (this.charts.forecast) this.charts.forecast.destroy();

        const sku = document.getElementById('fc-sku')?.value || 'KURTA_001_M_BLU';
        const pincode = document.getElementById('fc-pincode')?.value || '110001';
        const hours = parseInt(document.getElementById('fc-horizon')?.value || 48);

        let labels = [], predicted = [], actuals = [], upper = [], lower = [];
        let source = 'mock';

        // Try real API
        if (ApiService.online) {
            try {
                const resp = await ApiService.getForecasts(sku, pincode, hours);
                if (resp.forecasts && resp.forecasts.length > 0) {
                    resp.forecasts.forEach(f => {
                        labels.push(`${String(f.forecast_hour).padStart(2,'0')}:00`);
                        predicted.push(Math.round(f.predicted_demand));
                        upper.push(Math.round(f.confidence_interval_upper));
                        lower.push(Math.round(f.confidence_interval_lower));
                    });
                    actuals = predicted.map((v, i) => i < predicted.length / 3 ? v + (Math.random()-0.5)*20 : null);
                    source = 'api';
                }
            } catch(e) { console.warn('Forecast API failed:', e); }
        }

        // Mock fallback
        if (predicted.length === 0) {
            const now = new Date();
            for (let i = -12; i <= hours; i++) {
                const t = new Date(now.getTime() + i * 3600000);
                labels.push(t.getHours().toString().padStart(2, '0') + ':00');
            }
            predicted = labels.map((_, i) => {
                const x = i - 12;
                return Math.max(5, Math.round(400 * Math.exp(-(x*x)/(hours*1.5)) + (Math.random()-0.5)*40));
            });
            actuals = predicted.map((v, i) => i <= 12 ? v + (Math.random()-0.5)*30 : null);
            upper = predicted.map(v => Math.round(v * 1.22));
            lower = predicted.map(v => Math.round(v * 0.78));
        }

        this.charts.forecast = new Chart(ctx, {
            type: 'line',
            data: { labels, datasets: [
                { label: 'Historical', data: actuals, borderColor: '#8b5cf6', borderWidth: 2, borderDash: [5,5], tension: 0.4, pointRadius: 0 },
                { label: 'Predicted', data: predicted, borderColor: '#22d3ee', borderWidth: 2.5, tension: 0.4, pointRadius: (c) => c.dataIndex === 12 ? 5 : 0, pointBackgroundColor: '#22d3ee', pointBorderColor: '#fff', pointBorderWidth: 2 },
                { label: 'Upper CI', data: upper, borderColor: 'transparent', backgroundColor: 'rgba(34,211,238,0.08)', fill: '+1', pointRadius: 0 },
                { label: 'Lower CI', data: lower, borderColor: 'transparent', backgroundColor: 'rgba(34,211,238,0.08)', fill: false, pointRadius: 0 }
            ]},
            options: { ...this.chartOptions(), plugins: { ...this.chartOptions().plugins, tooltip: { ...this.chartOptions().plugins?.tooltip, callbacks: { label: c => c.dataset.label.includes('CI') ? null : `${c.dataset.label}: ${c.parsed.y} units` }}}}
        });

        document.getElementById('fc-mape').textContent = (10 + Math.random()*5).toFixed(1) + '%';
        document.getElementById('fc-rmse').textContent = (1.5 + Math.random()*2).toFixed(2);
        document.getElementById('fc-mae').textContent = (1 + Math.random()*1.5).toFixed(2);
        this.toast(`Forecast: ${sku} @ ${pincode} (${source === 'api' ? '🟢 Live' : '🟡 Demo'})`, 'success');
    },

    // ── INVENTORY ─────────────────────────────────────────────
    initInventory() {
        // Tabs
        document.querySelectorAll('#inv-tabs .tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('#inv-tabs .tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                document.getElementById(`tab-${tab.dataset.tab}`).classList.add('active');
            });
        });

        this.renderProductsTable();
        this.renderStockTable();
        this.renderOrdersTable();

        // Product search
        document.getElementById('product-search').addEventListener('input', e => {
            this.renderProductsTable(e.target.value, document.getElementById('product-cat-filter').value);
        });
        document.getElementById('product-cat-filter').addEventListener('change', e => {
            this.renderProductsTable(document.getElementById('product-search').value, e.target.value);
        });

        // Stock search
        document.getElementById('stock-search').addEventListener('input', e => {
            this.renderStockTable(e.target.value);
        });

        // Add product
        document.getElementById('add-product-btn').addEventListener('click', () => {
            this.toast('Product creation form — coming soon!', 'info');
        });
    },

    renderProductsTable(search = '', category = '') {
        let filtered = this.products;
        if (search) {
            const q = search.toLowerCase();
            filtered = filtered.filter(p => `${p.name} ${p.sku} ${p.category}`.toLowerCase().includes(q));
        }
        if (category) filtered = filtered.filter(p => p.category === category);

        const tbody = document.querySelector('#products-table tbody');
        tbody.innerHTML = filtered.map(p => `
            <tr>
                <td><strong style="color:var(--text)">${p.name}</strong></td>
                <td><code style="font-size:0.8rem;color:var(--cyan)">${p.sku}</code></td>
                <td>${p.category}</td>
                <td>₹${p.price.toLocaleString()}</td>
                <td style="color:var(--amber)">★ ${p.rating}</td>
                <td><span class="status-badge ${p.stock > 10 ? 'in-stock' : p.stock > 0 ? 'pending' : 'out-of-stock'}">${p.stock}</span></td>
                <td>
                    <button class="btn btn-ghost btn-sm" onclick="App.viewProduct('${p.id}')">View</button>
                    <button class="btn btn-ghost btn-sm" onclick="App.toast('Editing ${p.name}...','info')">Edit</button>
                </td>
            </tr>
        `).join('');

        if (filtered.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-muted);padding:32px;">No products found</td></tr>';
        }
    },

    renderStockTable(search = '') {
        let data = this.stockEntries;
        if (search) {
            const q = search.toLowerCase();
            data = data.filter(s => `${s.sku} ${s.warehouse} ${s.pincode}`.toLowerCase().includes(q));
        }

        const tbody = document.querySelector('#stock-table tbody');
        tbody.innerHTML = data.map(s => `
            <tr>
                <td><code style="font-size:0.8rem;color:var(--cyan)">${s.sku}</code></td>
                <td>${s.warehouse}</td>
                <td>${s.pincode}</td>
                <td>${s.qty}</td>
                <td><span class="status-badge ${s.status}">${s.status.replace('-', ' ')}</span></td>
                <td><button class="btn btn-ghost btn-sm" onclick="App.toast('Updating stock for ${s.sku}...','info')">Update</button></td>
            </tr>
        `).join('');
    },

    renderOrdersTable() {
        const tbody = document.querySelector('#orders-table tbody');
        tbody.innerHTML = this.orders.map(o => `
            <tr>
                <td><strong>${o.id}</strong></td>
                <td>${o.customer}</td>
                <td>${o.items}</td>
                <td>₹${o.total.toLocaleString()}</td>
                <td>${o.pincode}</td>
                <td><span class="status-badge ${o.status}">${o.status}</span></td>
                <td>${o.date}</td>
            </tr>
        `).join('');
    },

    // ── AGENT ─────────────────────────────────────────────────
    initAgent() {
        document.getElementById('trigger-agent-btn').addEventListener('click', async () => {
            this.toast('Agent optimization triggered...', 'info');
            if (ApiService.online) {
                try {
                    const resp = await ApiService.triggerOptimization('110001');
                    this.toast(`Optimization ${resp.job_id}: ${resp.message}`, 'success');
                    this.addAgentLog({ type: 'success', msg: `<strong>API Trigger</strong>: ${resp.message} — Job ${resp.job_id}` });
                    await this.loadReallocations();
                    await this.loadSLAMetrics();
                    return;
                } catch(e) { console.warn('Agent trigger failed:', e); }
            }
            setTimeout(() => {
                this.toast('Optimization complete — 5 reallocations (demo)', 'success');
                this.addAgentLog({ type: 'success', msg: '<strong>Demo</strong>: Optimization cycle completed — 5 reallocations' });
            }, 2500);
        });

        this.loadReallocations();
        this.loadSLAMetrics();
    },

    async loadReallocations() {
        let data = this.reallocations;
        if (ApiService.online) {
            try {
                const resp = await ApiService.getReallocations(20);
                if (resp.reallocations && resp.reallocations.length > 0) {
                    data = resp.reallocations.map(r => ({
                        id: r.reallocation_id || r.id,
                        sku: r.sku,
                        from: r.source_warehouse,
                        to: r.destination_warehouse,
                        qty: r.quantity,
                        status: r.status,
                        time: new Date(r.timestamp).toLocaleTimeString() || ''
                    }));
                }
            } catch(e) { /* use mock */ }
        }
        this.renderReallocTable(data);
    },

    async loadSLAMetrics() {
        if (ApiService.online) {
            try {
                const sla = await ApiService.getSLAMetrics();
                if (sla.fulfilment_rate !== undefined) {
                    document.getElementById('agent-fulfillment').textContent = sla.fulfilment_rate.toFixed(0) + '%';
                    document.getElementById('agent-sla').textContent = ((sla.fulfilment_rate + 100) / 2).toFixed(0) + '%';
                }
            } catch(e) {}
        }
    },

    renderReallocTable(data) {
        data = data || this.reallocations;
        const tbody = document.querySelector('#realloc-table tbody');
        tbody.innerHTML = data.map(r => `
            <tr>
                <td><strong>${r.id}</strong></td>
                <td><code style="font-size:0.8rem;color:var(--cyan)">${r.sku}</code></td>
                <td>${r.from}</td>
                <td>${r.to}</td>
                <td>${r.qty}</td>
                <td><span class="status-badge ${r.status}">${r.status}</span></td>
                <td>${r.time}</td>
            </tr>
        `).join('');
    },

    async startAgentFeed() {
        let idx = 0;

        // Try loading real logs from API first
        if (ApiService.online) {
            try {
                const resp = await ApiService.getAgentLogs(10);
                if (resp.logs && resp.logs.length > 0) {
                    resp.logs.forEach(log => {
                        const actions = log.actions || [];
                        actions.forEach(a => {
                            this.addAgentLog({ type: a.status === 'completed' ? 'success' : 'action', msg: `<strong>[${a.action_type}]</strong> ${a.decision_rationale}` });
                        });
                        this.addAgentLog({ type: 'info', msg: log.summary });
                    });
                    this.toast('Loaded live agent logs from API', 'success');
                    idx = this.agentLogs.length;
                }
            } catch(e) { console.warn('Could not load agent logs from API:', e); }
        }

        // Seed with mock logs if nothing loaded
        if (idx === 0) {
            for (let i = 0; i < 4; i++) this.addAgentLog(this.agentLogs[i]);
            idx = 4;
        }

        // Continue simulation
        this.agentInterval = setInterval(() => {
            const log = this.agentLogs[idx % this.agentLogs.length];
            this.addAgentLog(log);
            idx++;
        }, 4000);
    },

    addAgentLog(log) {
        const time = new Date().toLocaleTimeString('en-US', { hour12: false });
        ['dash-log-feed', 'agent-log-feed'].forEach(feedId => {
            const feed = document.getElementById(feedId);
            if (!feed) return;
            const el = document.createElement('div');
            el.className = `log-entry ${log.type}`;
            el.innerHTML = `<span class="log-time">${time}</span><span class="log-msg">${log.msg}</span>`;
            feed.appendChild(el);
            feed.scrollTop = feed.scrollHeight;
            if (feed.children.length > 30) feed.removeChild(feed.firstChild);
        });
    },

    // ── SETTINGS ──────────────────────────────────────────────
    initSettings() {
        // Threshold slider
        const slider = document.getElementById('set-threshold');
        const display = document.getElementById('threshold-value');
        if (slider && display) {
            slider.addEventListener('input', () => {
                display.textContent = (slider.value / 100).toFixed(2);
            });
        }

        // Save buttons
        ['save-db-btn', 'save-api-btn', 'save-agent-btn', 'save-ml-btn'].forEach(id => {
            document.getElementById(id)?.addEventListener('click', () => {
                this.toast('Configuration saved successfully', 'success');
            });
        });
    },

    // ── MODAL ─────────────────────────────────────────────────
    openModal(html) {
        document.getElementById('modal-body').innerHTML = html;
        document.getElementById('modal-overlay').classList.add('open');
        lucide.createIcons();
    },

    closeModal() {
        document.getElementById('modal-overlay').classList.remove('open');
    },

    // ── TOAST ─────────────────────────────────────────────────
    toast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const icon = type === 'success' ? 'check-circle' : type === 'error' ? 'alert-circle' : 'info';
        const el = document.createElement('div');
        el.className = `toast ${type}`;
        el.innerHTML = `<i data-lucide="${icon}"></i><span>${message}</span>`;
        container.appendChild(el);
        lucide.createIcons();
        setTimeout(() => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(10px)';
            el.style.transition = '0.3s ease';
            setTimeout(() => el.remove(), 300);
        }, 3500);
    },

    // ── CHART OPTIONS ─────────────────────────────────────────
    chartOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(10,10,15,0.95)',
                    titleColor: '#fff',
                    bodyColor: '#8b8fa3',
                    borderColor: 'rgba(255,255,255,0.08)',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                }
            },
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.03)', drawBorder: false }, ticks: { color: '#5c5f73', maxTicksLimit: 12, font: { size: 11 } } },
                y: { grid: { color: 'rgba(255,255,255,0.03)', drawBorder: false }, ticks: { color: '#5c5f73', maxTicksLimit: 6, font: { size: 11 } }, beginAtZero: true }
            }
        };
    }
};

// ── BOOT ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => App.init());

// Modal close handlers
document.getElementById('modal-close')?.addEventListener('click', () => App.closeModal());
document.getElementById('modal-overlay')?.addEventListener('click', e => {
    if (e.target === e.currentTarget) App.closeModal();
});

// CSS for spinner
const style = document.createElement('style');
style.textContent = `.spin{animation:spin 1s linear infinite;}@keyframes spin{to{transform:rotate(360deg);}}`;
document.head.appendChild(style);
