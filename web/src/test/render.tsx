/** Renders a page the way the router mounts it, with one account selected. */

import { render } from "@testing-library/react";
import { MemoryRouter, Outlet, Route, Routes } from "react-router-dom";

export const TEST_ACCOUNT = "11111111-2222-3333-4444-555555555555";

function Shell({ accountId }: { accountId: string | null }) {
  return <Outlet context={{ accountId }} />;
}

export function renderPage(
  element: React.ReactNode,
  accountId: string | null = TEST_ACCOUNT,
) {
  return render(
    <MemoryRouter>
      <Routes>
        <Route element={<Shell accountId={accountId} />}>
          <Route index element={element} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}
