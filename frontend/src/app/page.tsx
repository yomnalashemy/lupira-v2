import Link from "next/link";
import { FlaskConical, HelpCircle, Stethoscope, type LucideIcon } from "lucide-react";
import DisclaimerBanner from "@/components/DisclaimerBanner";

export default function HomePage() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-12 space-y-8">
      <div>
        <h1 className="text-3xl font-semibold text-primary">Lupira</h1>
        <p className="mt-3 text-lg text-foreground/80 leading-relaxed">
          Lupus (SLE) is an autoimmune condition that&rsquo;s notoriously hard to pin down — its symptoms
          overlap with dozens of other illnesses. Lupira helps make sense of a specific blood test that
          looks directly at gene activity linked to lupus, and explains what a result means in plain
          language.
        </p>
        <p className="mt-3 text-sm text-foreground/60">
          It&rsquo;s a research and education tool, not a replacement for your doctor — but it can help you
          understand a result you already have, or figure out what to ask for next.
        </p>
      </div>

      <DisclaimerBanner />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <ChoiceCard
          href="/predict?mode=upload"
          icon={FlaskConical}
          title="I have test results"
          desc="Upload the file from your lab or doctor's blood test — we'll handle the technical analysis."
        />
        <ChoiceCard
          href="/predict?mode=guide"
          icon={HelpCircle}
          title="I don't have test results yet"
          desc="Not sure where to start? We'll explain what this test looks for and how to get one."
        />
      </div>

      <div className="rounded border border-border bg-card p-5 shadow-soft">
        <div className="flex items-start gap-3">
          <Stethoscope className="mt-0.5 h-5 w-5 flex-shrink-0 text-accent" />
          <div>
            <h2 className="font-medium text-primary">Already diagnosed with lupus?</h2>
            <p className="mt-1 text-sm text-foreground/70">
              If you&rsquo;re tracking neurological or psychiatric symptoms, try the{" "}
              <Link href="/npsle" className="text-accent underline">
                symptom screening
              </Link>{" "}
              — a separate checklist based on established clinical criteria.
            </p>
          </div>
        </div>
      </div>

      <p className="text-xs text-foreground/50">
        Curious about the methodology, the data, or how accurate this is?{" "}
        <Link href="/about" className="underline">
          Read about the research
        </Link>
        .
      </p>
    </div>
  );
}

function ChoiceCard({ href, icon: Icon, title, desc }: { href: string; icon: LucideIcon; title: string; desc: string }) {
  return (
    <Link
      href={href}
      className="block rounded border border-border bg-card p-5 shadow-soft transition-colors hover:border-accent"
    >
      <Icon className="h-6 w-6 text-accent" />
      <h2 className="mt-3 font-medium text-primary">{title}</h2>
      <p className="mt-1 text-sm text-foreground/60">{desc}</p>
    </Link>
  );
}
