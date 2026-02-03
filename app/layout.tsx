import type { Metadata } from "next";
import "./main.css";

export const metadata: Metadata = {
  title: "네이버 서로이웃 자동 신청",
  description: "네이버 블로그 서로이웃 자동 신청 프로그램",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <head>
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css"
        />
      </head>
      <body className="antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
