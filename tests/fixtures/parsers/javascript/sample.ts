/**
 * @fileoverview Sample TypeScript file used for parser and AST analysis tests.
 */

import React, { useState, useEffect } from 'react';
import { Button } from './Button';
import * as fs from 'node:fs';

/**
 * Base service class defining shared lifecycle hooks.
 */
export class BaseService {
  protected isInitialized: boolean = false;

  public initialize(): void {
    this.isInitialized = true;
  }
}

/**
 * User data contract.
 */
export interface User {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  role?: string;
}

/**
 * Properties accepted by UserCard component.
 */
export type Props = {
  title: string;
};

/**
 * Service managing user authentication sessions.
 */
export class AuthService extends BaseService {
  private currentToken: string | null = null;

  /**
   * Log into the system using credentials.
   * @param username The account identifier
   * @param password The account secret
   * @returns Whether authentication was successful
   */
  public login(username: string, password: string): boolean {
    if (username.length > 0 && password.length > 0) {
      this.currentToken = `token_${Date.now()}`;
      return true;
    }
    return false;
  }

  /**
   * Log out of the system and invalidate active session.
   * @returns Promise that resolves when logout completes
   */
  public async logout(): Promise<void> {
    this.currentToken = null;
  }
}

/**
 * Formats user entity into a full display name string.
 * @param user The user entity
 * @returns Full name representation
 */
export function formatName(user: User): string {
  return `${user.firstName} ${user.lastName}`.trim();
}

/**
 * Checks if a user has administrative privileges.
 * @param user The user to check
 * @returns True if user has admin role
 */
export const isAdmin = (user: User): boolean => {
  return user.role === 'admin';
};

/**
 * Functional component displaying a user card banner.
 * @param props Component properties containing the title
 * @returns React element representing user card
 */
export const UserCard: React.FC<Props> = ({ title }) => {
  const [active, setActive] = useState<boolean>(false);

  useEffect(() => {
    setActive(true);
  }, []);

  return (
    <div className="card">
      <h2>{title}</h2>
      <Button onClick={() => setActive(!active)}>Toggle Status</Button>
    </div>
  );
};
