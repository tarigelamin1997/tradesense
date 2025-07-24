import { redirect } from "@sveltejs/kit";
const load = async ({ locals }) => {
  if (!locals.isAuthenticated) {
    throw redirect(303, "/login");
  }
  return {
    user: locals.user
  };
};
export {
  load
};
