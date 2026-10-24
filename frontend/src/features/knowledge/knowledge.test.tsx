import { fireEvent, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { apiMock } from "@/test/api-mock";
import { admin, employee, renderApp } from "@/test/render-app";
import { DocumentList } from "./components/document-list";
import { DocumentRow } from "./components/document-row";
import { KnowledgeCenter } from "./components/knowledge-center";

const doc = (id: string, title: string, status: string, category = "policy") => ({
  id,
  title,
  category,
  original_filename: `${id}.pdf`,
  content_type: "application/pdf",
  file_size_bytes: 2_500_000,
  status,
  error_message: status === "failed" ? "boom" : null,
  updated_at: new Date().toISOString(),
  created_at: new Date().toISOString(),
});
const documents = (items: ReturnType<typeof doc>[], total = items.length) => ({ items, total, page: 1, page_size: 100 });

describe("KnowledgeCenter", () => {
  it("invites an admin to upload when there are no documents, with the form right there", async () => {
    apiMock.on("GET", "/knowledge/documents", documents([]));
    renderApp(<KnowledgeCenter canManage />, { user: admin() });

    expect(await screen.findByText(/Teach Compass/)).toBeInTheDocument();
    expect(screen.getByText("Choose a PDF, DOCX or TXT file")).toBeInTheDocument();
  });

  it("tells everyone else to ask an admin, with no upload form", async () => {
    apiMock.on("GET", "/knowledge/documents", documents([]));
    renderApp(<KnowledgeCenter canManage={false} />, { user: employee() });

    expect(await screen.findByText(/An admin can add them here/)).toBeInTheDocument();
    expect(screen.queryByText("Choose a PDF, DOCX or TXT file")).not.toBeInTheDocument();
  });

  it("shows Compass, honest counts, and the library grouped by category", async () => {
    apiMock.on("GET", "/knowledge/documents", documents([doc("1", "Remote Work Policy", "ready"), doc("2", "Benefits Guide", "failed", "benefits")]));
    renderApp(<KnowledgeCenter canManage />, { user: admin() });

    expect(await screen.findByText(/Ask anything about your company/)).toBeInTheDocument();
    expect(screen.getByText("2 documents · 1 ready for Compass")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Benefits" })).toBeInTheDocument();
    expect(screen.getByText("boom")).toBeInTheDocument();
  });

  it("builds Compass's suggestions from documents that are actually ready", async () => {
    apiMock.on("GET", "/knowledge/documents", documents([doc("1", "Remote Work Policy", "ready"), doc("2", "Benefits Guide", "failed", "benefits")]));
    renderApp(<KnowledgeCenter canManage />, { user: admin() });

    expect(await screen.findByText("What does “Remote Work Policy” cover?")).toBeInTheDocument();
    expect(screen.queryByText("What does “Benefits Guide” cover?")).not.toBeInTheDocument();
  });

  it("keeps the upload form hidden until asked for", async () => {
    apiMock.on("GET", "/knowledge/documents", documents([doc("1", "Handbook", "ready")]));
    renderApp(<KnowledgeCenter canManage />, { user: admin() });
    await screen.findByText(/Ask anything about your company/);
    expect(screen.queryByText("Choose a PDF, DOCX or TXT file")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Upload document" }));

    expect(screen.getByText("Choose a PDF, DOCX or TXT file")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Close" })).toBeInTheDocument();
  });

  it("explains documents that are still processing, without showing a Compass box", async () => {
    apiMock.on("GET", "/knowledge/documents", documents([doc("3", "Pending", "embedded")]));
    renderApp(<KnowledgeCenter canManage />, { user: admin() });

    expect(await screen.findByText(/still being processed/)).toBeInTheDocument();
    expect(screen.queryByText(/Ask anything about your company/)).not.toBeInTheDocument();
  });

  it("says plainly when none of the documents could be processed", async () => {
    apiMock.on("GET", "/knowledge/documents", documents([doc("4", "Bad", "failed")]));
    renderApp(<KnowledgeCenter canManage />, { user: admin() });

    expect(await screen.findByText(/None of the documents could be processed/)).toBeInTheDocument();
  });

  it("is honest when the library is bigger than what was fetched", async () => {
    apiMock.on("GET", "/knowledge/documents", documents([doc("5", "A", "ready")], 150));
    renderApp(<KnowledgeCenter canManage />, { user: admin() });

    expect(await screen.findByText("Showing the first 1 of 150 documents.")).toBeInTheDocument();
  });
});

describe("DocumentList", () => {
  const docs = [doc("1", "Policy A", "ready"), doc("2", "Benefit B", "ready", "benefits"), doc("3", "Other C", "ready", "other")] as never[];

  it("groups by category in a fixed, sensible order", () => {
    renderApp(<DocumentList documents={docs} canManage={false} />, { user: employee() });

    const headings = screen.getAllByRole("heading").map((h) => h.textContent);
    expect(headings).toEqual(["Policy", "Benefits", "Other"]);
  });

  it("filters by category using counts from the same documents", () => {
    renderApp(<DocumentList documents={docs} canManage={false} />, { user: employee() });

    fireEvent.click(screen.getByRole("button", { name: /Benefits/ }));

    expect(screen.getByText("Benefit B")).toBeInTheDocument();
    expect(screen.queryByText("Policy A")).not.toBeInTheDocument();
  });

  it("hides management actions from people who cannot manage", () => {
    renderApp(<DocumentList documents={docs} canManage={false} />, { user: employee() });

    expect(screen.queryByRole("button", { name: "Delete" })).not.toBeInTheDocument();
  });
});

describe("DocumentRow", () => {
  const setup = () => {
    apiMock.on("DELETE", "/knowledge/documents/d1", { status: 204 });
    apiMock.on("POST", "/knowledge/documents/d1/reindex", doc("d1", "Handbook", "ready"));
    renderApp(
      <ul>
        <DocumentRow document={doc("d1", "Handbook", "ready") as never} canManage />
      </ul>,
      { user: admin() },
    );
  };

  it("shows the file type, real size and status", () => {
    setup();

    expect(screen.getByText("PDF")).toBeInTheDocument();
    expect(screen.getByText(/2\.4 MB/)).toBeInTheDocument();
  });

  it("asks before deleting and hides other actions meanwhile", () => {
    setup();
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));

    expect(screen.getByRole("button", { name: "Confirm delete" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Reindex" })).not.toBeInTheDocument();
    expect(apiMock.writes).toHaveLength(0);

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.getByRole("button", { name: "Reindex" })).toBeInTheDocument();
    expect(apiMock.writes).toHaveLength(0);
  });

  it("deletes once confirmed and says so", async () => {
    setup();
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirm delete" }));

    expect(await screen.findByText("Document deleted")).toBeInTheDocument();
    expect(apiMock.find("DELETE", "/knowledge/documents/d1")).toBeDefined();
  });

  it("reindexes in one click", async () => {
    setup();
    fireEvent.click(screen.getByRole("button", { name: "Reindex" }));

    await waitFor(() => expect(apiMock.find("POST", "/knowledge/documents/d1/reindex")).toBeDefined());
    expect(await screen.findByText("Reindexing started")).toBeInTheDocument();
  });
});
