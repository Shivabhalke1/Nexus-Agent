"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { apiRequest } from "./api-client";

export interface Product {
  id: number;
  name: string;
  slug: string;
  description: string;
  price: string | number;
  stock: number;
  sku: string;
  image_url: string;
  is_active: boolean;
  category?: {
    id: number;
    name: string;
    slug: string;
  };
}

export interface CartItem {
  id: number;
  cart_id: number;
  product_id: number;
  quantity: number;
  unit_price: string | number;
  subtotal: string | number;
  product?: Product;
}

export interface Cart {
  id: number;
  items: CartItem[];
  total_items: number;
  total_amount: string | number;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
}

interface CartContextType {
  cart: Cart | null;
  user: User | null;
  isLoading: boolean;
  addToCart: (productId: number, quantity?: number) => Promise<boolean>;
  updateQuantity: (itemId: number, quantity: number) => Promise<boolean>;
  removeFromCart: (itemId: number) => Promise<boolean>;
  clearCart: () => Promise<boolean>;
  refreshCart: () => Promise<void>;
  setUserSession: (user: User | null, token?: string) => void;
  logout: () => void;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export function CartProvider({ children }: { children: React.ReactNode }) {
  const [cart, setCart] = useState<Cart | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize session and load cart
  useEffect(() => {
    if (typeof window !== "undefined") {
      let session = localStorage.getItem("nexus_session_id");
      if (!session) {
        session = "sess_" + Math.random().toString(36).substring(2, 12);
        localStorage.setItem("nexus_session_id", session);
      }

      const storedUser = localStorage.getItem("nexus_user");
      if (storedUser) {
        try {
          setUser(JSON.parse(storedUser));
        } catch (e) {}
      }
    }
    refreshCart();
  }, []);

  const refreshCart = async () => {
    setIsLoading(true);
    const res = await apiRequest<Cart>("/cart");
    if (res.success && res.data) {
      setCart(res.data);
    } else {
      setCart({
        id: 0,
        items: [],
        total_items: 0,
        total_amount: "0.00",
      });
    }
    setIsLoading(false);
  };

  const addToCart = async (productId: number, quantity = 1): Promise<boolean> => {
    const res = await apiRequest<Cart>("/cart/items", {
      method: "POST",
      body: JSON.stringify({ product_id: productId, quantity }),
    });
    if (res.success && res.data) {
      setCart(res.data);
      return true;
    }
    return false;
  };

  const updateQuantity = async (itemId: number, quantity: number): Promise<boolean> => {
    if (quantity <= 0) return removeFromCart(itemId);
    const res = await apiRequest<Cart>(`/cart/items/${itemId}`, {
      method: "PUT",
      body: JSON.stringify({ quantity }),
    });
    if (res.success && res.data) {
      setCart(res.data);
      return true;
    }
    return false;
  };

  const removeFromCart = async (itemId: number): Promise<boolean> => {
    const res = await apiRequest<Cart>(`/cart/items/${itemId}`, {
      method: "DELETE",
    });
    if (res.success && res.data) {
      setCart(res.data);
      return true;
    }
    return false;
  };

  const clearCart = async (): Promise<boolean> => {
    const res = await apiRequest<Cart>("/cart", {
      method: "DELETE",
    });
    if (res.success && res.data) {
      setCart(res.data);
      return true;
    }
    return false;
  };

  const setUserSession = (newUser: User | null, token?: string) => {
    setUser(newUser);
    if (typeof window !== "undefined") {
      if (newUser && token) {
        localStorage.setItem("nexus_user", JSON.stringify(newUser));
        localStorage.setItem("nexus_token", token);
      } else {
        localStorage.removeItem("nexus_user");
        localStorage.removeItem("nexus_token");
      }
    }
    refreshCart();
  };

  const logout = () => {
    apiRequest("/auth/logout", { method: "POST" });
    setUserSession(null);
  };

  return (
    <CartContext.Provider
      value={{
        cart,
        user,
        isLoading,
        addToCart,
        updateQuantity,
        removeFromCart,
        clearCart,
        refreshCart,
        setUserSession,
        logout,
      }}
    >
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error("useCart must be used within a CartProvider");
  }
  return context;
}
