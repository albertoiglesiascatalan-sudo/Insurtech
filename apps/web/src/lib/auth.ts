import { getServerSession } from "next-auth";
import { authOptions } from "./auth-options";

export { authOptions };
export const getSession = () => getServerSession(authOptions);
