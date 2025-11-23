document.addEventListener('DOMContentLoaded', function() {
    let allProducts = []; 
    let cart = [];

    const productListContainer = document.getElementById('product-list-container');
    const cartItemsContainer = document.querySelector('.cart-items');
    const cartTotalElement = document.getElementById('cart-total');
    const checkoutBtn = document.getElementById('checkout-btn');

    const cusNameInput = document.getElementById('cus-name');
    const cusPhoneInput = document.getElementById('cus-phone');
    const cusAddressInput = document.getElementById('cus-address');
    const cusBranchInput = document.getElementById('cus-branch');
    const transportSelect = document.getElementById('transport-company');
    const paymentMethodSelect = document.getElementById('payment-method');

    // --- Helper Function: จัดรูปแบบตัวเลขเงิน LAK (มี Comma) ---
    function formatLAK(num) {
        // แปลงเป็นทศนิยม 2 ตำแหน่ง แล้วใช้ Regular Expression เติม Comma
        return 'LAK ' + num.toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
    }

    function fetchProducts() {
        fetch('/api/products')
            .then(response => response.json())
            .then(products => {
                allProducts = products;
                renderProducts(products);
            })
            .catch(error => {
                console.error('Error fetching products:', error);
                productListContainer.innerHTML = '<p>เกิดข้อผิดพลาดในการโหลดสินค้า</p>';
            });
    }

    function renderProducts(products) {
        productListContainer.innerHTML = '';
        if (products.length === 0) {
            productListContainer.innerHTML = '<p>ไม่พบสินค้าในระบบ</p>';
            return;
        }

        products.forEach(product => {
            const card = document.createElement('div');
            card.className = 'product-card pos-card pos-card-interactive';
            card.dataset.productId = product.id;

            const imagePath = product.image_file ? `/static/product_images/${product.image_file}` : '/static/product_images/default.jpg';
            
            // ใช้ formatLAK แสดงราคาบนการ์ด
            const formattedPrice = formatLAK(product.price);

            card.innerHTML = `
                <img src="${imagePath}" alt="${product.name}" class="pos-card-img">
                <div class="pos-card-details">
                    <h4><small>#${product.code}</small> ${product.name}</h4>
                    <p class="price">${formattedPrice}</p>
                    <p class="stock" data-stock="${product.stock}">สต็อก: ${product.stock}</p>
                </div>
            `;

            card.addEventListener('click', function() {
                const productId = parseInt(this.dataset.productId);
                addToCart(productId);
            });

            productListContainer.appendChild(card);
        });
    }

    function addToCart(productId) {
        const product = allProducts.find(p => p.id === productId);
        if (!product || product.stock <= 0) {
            alert("สินค้านี้หมดสต็อกหรือไม่พร้อมจำหน่าย");
            return;
        }

        const cartItem = cart.find(item => item.product.id === productId);
        if (cartItem) {
            if (cartItem.quantity + 1 > product.stock) {
                 alert("สินค้าในสต็อกมีไม่เพียงพอ!");
                 return;
            }
            cartItem.quantity++;
        } else {
            cart.push({ product: product, quantity: 1 });
        }
        renderCart();
    }

    function updateCartQuantity(index, newQuantity) {
        const item = cart[index];
        if (newQuantity > item.product.stock) {
            alert(`มีสินค้าในสต็อกเพียง ${item.product.stock} ชิ้น`);
            item.quantity = item.product.stock;
        } else if (newQuantity < 1) {
            removeFromCart(index);
            return;
        } else {
            item.quantity = newQuantity;
        }
        renderCart();
    }

    function renderCart() {
        cartItemsContainer.innerHTML = '';
        let total = 0;

        if (cart.length === 0) {
            cartItemsContainer.innerHTML = '<p>ยังไม่มีสินค้าในตะกร้า</p>';
            // ใช้ formatLAK แสดงยอดรวม 0
            cartTotalElement.textContent = formatLAK(0);
            checkoutBtn.disabled = true;
            return;
        }

        checkoutBtn.disabled = false;

        cart.forEach((item, index) => {
            const itemTotal = item.product.price * item.quantity;
            total += itemTotal;

            const cartItemEl = document.createElement('div');
            cartItemEl.className = 'cart-item';
            cartItemEl.style.display = 'flex';
            cartItemEl.style.justifyContent = 'space-between';
            cartItemEl.style.alignItems = 'center';
            cartItemEl.style.marginBottom = '10px';
            cartItemEl.style.paddingBottom = '10px';
            cartItemEl.style.borderBottom = '1px solid #eee';
            
            // ใช้ formatLAK แสดงราคาต่อชิ้น และราคารวมของรายการนั้น
            cartItemEl.innerHTML = `
                <div class="cart-item-info" style="flex: 1;">
                    <h4 style="margin: 0 0 5px 0;">${item.product.name}</h4>
                    <div style="display: flex; align-items: center;">
                        <input type="number" class="qty-input" min="1" max="${item.product.stock}" value="${item.quantity}" data-index="${index}" style="width: 60px; margin-right: 10px; padding: 5px; text-align: center;">
                        <span>x ${formatLAK(item.product.price)}</span>
                    </div>
                </div>
                <div class="cart-item-actions" style="display: flex; align-items: center;">
                    <strong class="item-total-price" style="margin-right: 15px;">${formatLAK(itemTotal)}</strong>
                    <button class="remove-btn" data-index="${index}" style="background: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">ลบ</button>
                </div>
            `;

            cartItemEl.querySelector('.qty-input').addEventListener('change', function() {
                const newQty = parseInt(this.value);
                updateCartQuantity(index, newQty);
            });

            cartItemEl.querySelector('.remove-btn').addEventListener('click', function(e) {
                e.stopPropagation(); 
                removeFromCart(parseInt(this.dataset.index));
            });

            cartItemsContainer.appendChild(cartItemEl);
        });

        // ใช้ formatLAK แสดงยอดรวมสุทธิ
        cartTotalElement.textContent = formatLAK(total);
    }

    function removeFromCart(index) {
        cart.splice(index, 1);
        renderCart();
    }

    checkoutBtn.addEventListener('click', async function() {
        if (cart.length === 0) return;

        if (!cusNameInput.value.trim()) {
            alert("กรุณาระบุชื่อลูกค้า");
            cusNameInput.focus();
            return;
        }

        this.disabled = true;
        this.textContent = 'กำลังบันทึก...';

        const cartDataForServer = cart.map(item => ({
            productId: item.product.id,
            quantity: item.quantity
        }));

        const customerData = {
            name: cusNameInput.value.trim(),
            phone: cusPhoneInput.value.trim(),
            address: cusAddressInput.value.trim(),
            branch: cusBranchInput.value.trim(),
            transport: transportSelect.value,
            paymentMethod: paymentMethodSelect.value
        };

        try {
            const response = await fetch('/api/checkout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    cart: cartDataForServer,
                    customer: customerData
                })
            });
            const result = await response.json();
            if (result.success) {
                cart = [];
                renderCart();
                fetchProducts(); 
                cusNameInput.value = '';
                cusPhoneInput.value = '';
                cusAddressInput.value = '';
                cusBranchInput.value = '';
                transportSelect.value = '';
                paymentMethodSelect.value = 'Transfer';

                alert(`บันทึกรายการขายสำเร็จ! เลขที่ออเดอร์: #${result.order_id}`);

            } else {
                alert(`เกิดข้อผิดพลาด: ${result.message}`);
            }
        } catch (error) {
            console.error('Error during checkout:', error);
            alert('เกิดข้อผิดพลาดในการเชื่อมต่อกับเซิร์ฟเวอร์');
        } finally {
            this.disabled = false;
            this.textContent = 'ชำระเงิน (Checkout)';
        }
    });

    fetchProducts();
});