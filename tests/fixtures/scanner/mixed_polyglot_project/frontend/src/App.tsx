import React, { useState } from 'react';
import { Header } from './components/Header';
import { ItemList, Item } from './components/ItemList';

const INITIAL_ITEMS: Item[] = [
  { id: 1, name: 'Mechanical Keyboard', price: 129.99, in_stock: true },
  { id: 2, name: 'Wireless Mouse', price: 49.99, in_stock: true },
  { id: 3, name: 'USB-C Monitor Hub', price: 89.99, in_stock: false },
];

/**
 * Root application component coordinating header and item list views.
 */
export const App: React.FC = () => {
  const [items] = useState<Item[]>(INITIAL_ITEMS);

  return (
    <div className="app-layout">
      <Header title="Polyglot Inventory Dashboard" subtitle="Item catalog & status" />
      <main className="content-container">
        <ItemList items={items} />
      </main>
    </div>
  );
};

export default App;
