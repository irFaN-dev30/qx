import './globals.css';

export const metadata = {
  title: 'Trade Signal Terminal',
  description: 'Lightweight, high-performance trading signal monitor',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
