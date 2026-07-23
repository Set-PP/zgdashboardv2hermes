import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import Marquee from "@/components/Marquee";
import Projects from "@/components/Projects";
import Updates from "@/components/Updates";
import Stats from "@/components/Stats";
import Studio from "@/components/Studio";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <main>
      <Navbar />
      <Hero />
      <Marquee />
      <Projects />
      <Updates />
      <Stats />
      <Studio />
      <Footer />
    </main>
  );
}
