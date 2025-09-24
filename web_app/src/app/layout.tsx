import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({
  variable: '--font-inter',
  subsets: ['latin'],
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Secfix Policy Configuration',
  description: 'Automated policy customization',
  keywords: ['policy', 'automation', 'AI', 'Secfix', 'document', 'customization'],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang='en' className='bg-gray-50'>
      <body className={`${inter.variable} antialiased bg-gray-50`}>{children}</body>
    </html>
  );
}
