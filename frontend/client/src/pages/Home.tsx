import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { Streamdown } from "streamdown";
import { useI18n } from "@/i18n";
import { Link } from "wouter";

/**
 * All content in this page are only for example, replace with your own feature implementation
 * When building pages, remember your instructions in Frontend Best Practices, Design Guide and Common Pitfalls
 */
export default function Home() {
  const { t } = useI18n();

  // If theme is switchable in App.tsx, we can implement theme toggling like this:
  // const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen flex flex-col">
      <main>
        {/* Example: lucide-react for icons */}
        <Loader2 className="animate-spin" />
        <h1>{t("home.title")}</h1>
        {/* Example: Streamdown for markdown rendering */}
        <Streamdown>{t("home.description")}</Streamdown>
        <Button asChild variant="default">
          <Link href="/home">{t("home.cta")}</Link>
        </Button>
      </main>
    </div>
  );
}
