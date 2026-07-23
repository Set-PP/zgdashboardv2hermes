import { redirect } from "next/navigation";

// v1 client portal superseded by the access-code portal
export default function DashboardRedirect() {
  redirect("/portal");
}
