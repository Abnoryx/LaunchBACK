import './globals.css'
export const metadata = { title: 'LaunchBack Library', description: 'Control the shot library' }
export default function Root({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>
}
