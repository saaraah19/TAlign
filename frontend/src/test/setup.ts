import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, beforeEach } from "vitest";
import { apiMock } from "./api-mock";

// jsdom knows the <dialog> element but not showModal()/close(), which the
// Compass panel relies on. This mimics what a browser does: set `open`,
// and fire `close` when closing.
HTMLDialogElement.prototype.showModal = function showModal() {
  this.setAttribute("open", "");
};
HTMLDialogElement.prototype.close = function close() {
  if (!this.hasAttribute("open")) return;
  this.removeAttribute("open");
  this.dispatchEvent(new Event("close"));
};

// A browser refuses to focus an element that is not being rendered, such
// as anything inside a <dialog> that is not open; jsdom focuses it anyway,
// which would hide exactly the bug the Compass panel's explicit focus call
// exists to fix (React's autoFocus runs while the dialog is still closed).
const realFocus = HTMLElement.prototype.focus;
HTMLElement.prototype.focus = function focus(options?: FocusOptions) {
  if (this.closest("dialog:not([open])")) return;
  realFocus.call(this, options);
};

// jsdom cannot navigate. Components that use <Link> go through the router
// mock, but a plain click on an <a href> would still make jsdom print a
// "Not implemented: navigation" error; cancel it after React has seen it.
document.addEventListener("click", (event) => {
  if ((event.target as Element).closest?.("a[href]")) event.preventDefault();
});

beforeEach(() => apiMock.reset());
afterEach(() => cleanup());
