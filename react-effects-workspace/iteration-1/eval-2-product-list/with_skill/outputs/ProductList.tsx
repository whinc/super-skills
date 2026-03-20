import { useState, useMemo, useCallback } from "react";

// --- Types ---

export interface Product {
  id: string;
  name: string;
  price: number;
}

interface ProductListProps {
  products: Product[];
  filter: string;
}

// --- Notification helper (simple toast-style) ---

function showNotification(message: string) {
  // In a real app this would use a toast library; here we use a simple alert
  // or a custom notification system.
  if (typeof window !== "undefined") {
    // Prefer a non-blocking approach if available
    console.log(`[Notification] ${message}`);
    alert(message);
  }
}

// --- Cart state (local to this module for simplicity) ---

const cart: Product[] = [];

function addToCart(product: Product) {
  cart.push(product);
}

// --- Component ---

export default function ProductList({ products, filter }: ProductListProps) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [prevFilter, setPrevFilter] = useState(filter);

  // Scenario 4 (Adjusting Some State When a Prop Changes):
  // When filter changes, clear the selection. This is a render-time state
  // adjustment — no useEffect needed. React will re-render with the reset
  // state immediately, so the user never sees stale selections.
  if (filter !== prevFilter) {
    setPrevFilter(filter);
    setSelectedIds(new Set());
  }

  // Scenario 2 (Caching Expensive Computations):
  // Filtered products are derived from props — compute during render.
  // useMemo avoids recomputation when products/filter haven't changed.
  const filteredProducts = useMemo(() => {
    const lowerFilter = filter.toLowerCase();
    return products.filter((product) =>
      product.name.toLowerCase().includes(lowerFilter)
    );
  }, [products, filter]);

  // Scenario 5 (Event-Specific Logic):
  // Adding to cart and showing a notification are direct responses to
  // user clicks — they belong in event handlers, not in Effects.
  const handleAddToCart = useCallback((product: Product) => {
    addToCart(product);
    showNotification(`Added "${product.name}" to cart!`);
  }, []);

  const handleToggleSelect = useCallback((productId: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(productId)) {
        next.delete(productId);
      } else {
        next.add(productId);
      }
      return next;
    });
  }, []);

  return (
    <div className="product-list">
      <h2>Products</h2>
      {filter && (
        <p className="filter-info">
          Filtering by: <strong>{filter}</strong>
        </p>
      )}

      {filteredProducts.length === 0 ? (
        <p className="empty-state">No products match the current filter.</p>
      ) : (
        <ul>
          {filteredProducts.map((product) => {
            const isSelected = selectedIds.has(product.id);
            return (
              <li
                key={product.id}
                className={`product-item ${isSelected ? "selected" : ""}`}
              >
                <label>
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => handleToggleSelect(product.id)}
                  />
                  <span className="product-name">{product.name}</span>
                  <span className="product-price">
                    ${product.price.toFixed(2)}
                  </span>
                </label>
                <button
                  type="button"
                  onClick={() => handleAddToCart(product)}
                  className="add-to-cart-btn"
                >
                  Add to Cart
                </button>
              </li>
            );
          })}
        </ul>
      )}

      {selectedIds.size > 0 && (
        <div className="selection-summary">
          <p>{selectedIds.size} product(s) selected</p>
        </div>
      )}
    </div>
  );
}
