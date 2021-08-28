import { createContext } from "react";

export type UserResponse = {
  user: string;
  balance: number;
  privKey: string;
  pubKey: string;
};

export const UserContext = createContext({
  users<UserResponse[]>: []
});
