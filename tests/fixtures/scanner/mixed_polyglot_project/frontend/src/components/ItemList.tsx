import React from 'react';
import { formatCurrency } from '../utils/format';

export interface Item {
  id: number;
  name: string;
  price: number;
  in_stock: boolean;
}

export interface ItemListProps {
  items: Item[];
}

/**
 * Functional component displaying a list of catalog items.
 */
export const ItemList: React.FC<ItemListProps> = ({ items }) => {
  return (
    <section className="item-list-container">
      <h2>Catalog Items ({items.length})</h2>
      <ul className="item-list">
        {items.map((item) => (
          <li key={item.id} className={`item-row ${item.in_stock ? 'in-stock' : 'out-of-stock'}`}>
            <span className="item-name">{item.name}</span>
            <span className="item-price">{formatCurrency(item.price)}</span>
            <span className="item-badge">{item.in_stock ? 'In Stock' : 'Out of Stock'}</span>
          </li>
        ))}
      </ul>
    </section>
  );
};
