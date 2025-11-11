// パン屋原価計算アプリ - メインJavaScript

document.addEventListener('DOMContentLoaded', function() {
    // アラートの自動消去
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // フォームバリデーション
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // 数値入力フィールドの負数防止
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(input => {
        input.addEventListener('keydown', function(e) {
            if (e.key === '-' || e.key === 'e' || e.key === 'E') {
                e.preventDefault();
            }
        });
    });

    // 確認ダイアログ
    const deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    // テーブルソート機能(簡易版)
    initTableSort();
});

// テーブルソート機能
function initTableSort() {
    const tables = document.querySelectorAll('table.sortable');
    tables.forEach(table => {
        const headers = table.querySelectorAll('th[data-sort]');
        headers.forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', function() {
                sortTable(table, this.dataset.sort);
            });
        });
    });
}

function sortTable(table, column) {
    // 簡易的なソート実装
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    rows.sort((a, b) => {
        const aValue = a.querySelector(`td:nth-child(${column})`).textContent;
        const bValue = b.querySelector(`td:nth-child(${column})`).textContent;
        return aValue.localeCompare(bValue, 'ja');
    });

    rows.forEach(row => tbody.appendChild(row));
}

// 通貨フォーマット
function formatCurrency(amount) {
    return new Intl.NumberFormat('ja-JP', {
        style: 'currency',
        currency: 'JPY'
    }).format(amount);
}

// パーセンテージフォーマット
function formatPercentage(value) {
    return value.toFixed(1) + '%';
}

// デバウンス関数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ローカルストレージへの保存
function saveToLocalStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
        console.error('LocalStorage save error:', e);
    }
}

// ローカルストレージからの読み込み
function loadFromLocalStorage(key) {
    try {
        const value = localStorage.getItem(key);
        return value ? JSON.parse(value) : null;
    } catch (e) {
        console.error('LocalStorage load error:', e);
        return null;
    }
}

// レスポンシブナビゲーション
function initResponsiveNav() {
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');

    if (navbarToggler && navbarCollapse) {
        navbarToggler.addEventListener('click', function() {
            navbarCollapse.classList.toggle('show');
        });

        // ナビゲーションリンクをクリックしたら自動で閉じる(モバイル)
        const navLinks = navbarCollapse.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                if (window.innerWidth < 992) {
                    navbarCollapse.classList.remove('show');
                }
            });
        });
    }
}

initResponsiveNav();
