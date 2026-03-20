import React, { useState, useEffect, useCallback, useMemo } from "react";

// ---------- Types ----------

export interface Product {
  id: string | number;
  name: string;
  price: number;
  category?: string;
}

export interface CartItem extends Product {
  quantity: number;
}

interface Notification {
  id: number;
  message: string;
}

interface ProductListProps {
  products: Product[];
  filter: string;
}

// ---------- Notification Toast ----------

function Toast({
  notification,
  onDismiss,
}: {
  notification: Notification;
  onDismiss: (id: number) => void;
}) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onDismiss(notification.id);
    }, 2500);
    return () => clearTimeout(timer);
  }, [notification.id, onDismiss]);

  return (
    <div
      role="status"
      style={{
        padding: "8px 16px",
        marginBottom: 8,
        backgroundColor: "#4caf50",
        color: "#fff",
        borderRadius: 4,
        boxShadow: "0 2px 6px rgba(0,0,0,0.2)",
        animation: "fadeIn 0.3s ease",
      }}
    >
      {notification.message}
    </div>
  );
}

// ---------- ProductList Component ----------

const ProductList: React.FC<ProductListProps> = ({ products, filter }) => {
  const [cart, setCart] = useState<CartItem[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [notificationCounter, setNotificationCounter] = useState(0);

  // Clear the cart whenever the filter changes
  useEffect(() => {
    setCart([]);
  }, [filter]);

  // Derived: filtered products based on the filter string
  const filteredProducts = useMemo(() => {
    if (!filter.trim()) return products;
    const lowerFilter = filter.toLowerCase();
    return products.filter(
      (p) =>
        p.name.toLowerCase().includes(lowerFilter) ||
        (p.category && p.category.toLowerCase().includes(lowerFilter)),
    );
  }, [products, filter]);

  // Dismiss a notification by id
  const dismissNotification = useCallback((id: number) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  // Add a product to the cart
  const addToCart = useCallback(
    (product: Product) => {
      setCart((prev) => {
        const existing = prev.find((item) => item.id === product.id);
        if (existing) {
          return prev.map((item) =>
            item.id === product.id
              ? { ...item, quantity: item.quantity + 1 }
              : item,
          );
        }
        return [...prev, { ...product, quantity: 1 }];
      });

      // Show notification
      const id = notificationCounter + 1;
      setNotificationCounter(id);
      setNotifications((prev) => [
        ...prev,
        { id, message: `"${product.name}" 已加入购物车` },
      ]);
    },
    [notificationCounter],
  );

  return (
    <div style={{ position: "relative", fontFamily: "sans-serif" }}>
      {/* Notifications */}
      <div
        style={{
          position: "fixed",
          top: 16,
          right: 16,
          zIndex: 1000,
        }}
      >
        {notifications.map((n) => (
          <Toast key={n.id} notification={n} onDismiss={dismissNotification} />
        ))}
      </div>

      {/* Cart summary */}
      <div
        style={{
          marginBottom: 16,
          padding: 12,
          backgroundColor: "#f5f5f5",
          borderRadius: 8,
        }}
      >
        <strong>购物车</strong>
        {cart.length === 0 ? (
          <span style={{ marginLeft: 8, color: "#999" }}>（空）</span>
        ) : (
          <span style={{ marginLeft: 8 }}>
            {cart.reduce((sum, item) => sum + item.quantity, 0)} 件商品 | 合计 ¥
            {cart
              .reduce((sum, item) => sum + item.price * item.quantity, 0)
              .toFixed(2)}
          </span>
        )}
      </div>

      {/* Product list */}
      {filteredProducts.length === 0 ? (
        <p style={{ color: "#999", textAlign: "center", padding: 24 }}>
          没有找到匹配的商品
        </p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
          {filteredProducts.map((product) => (
            <li
              key={product.id}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "12px 16px",
                borderBottom: "1px solid #eee",
              }}
            >
              <div>
                <span style={{ fontWeight: 500 }}>{product.name}</span>
                {product.category && (
                  <span
                    style={{ marginLeft: 8, color: "#888", fontSize: "0.85em" }}
                  >
                    [{product.category}]
                  </span>
                )}
                <span style={{ marginLeft: 12, color: "#e65100" }}>
                  ¥{product.price.toFixed(2)}
                </span>
              </div>
              <button
                onClick={() => addToCart(product)}
                style={{
                  padding: "6px 14px",
                  backgroundColor: "#1976d2",
                  color: "#fff",
                  border: "none",
                  borderRadius: 4,
                  cursor: "pointer",
                }}
              >
                加入购物车
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default ProductList;
