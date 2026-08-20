interface ErrorBannerProps {
  message: string;
}

// "Verification stopped." and the trailing sentence are static UI copy
// wrapping the raw verification_error -- confirmed against a real
// tampered-fixture response, which returns just the bare error
// ("targets was signed by 0/1 keys"), no boilerplate attached.
export function ErrorBanner({ message }: ErrorBannerProps) {
  return (
    <div className="error-banner" role="alert">
      <strong>Verification stopped.</strong> {message} Roles verified before this point are shown; the rest could
      not be checked, so they are not displayed.
    </div>
  );
}
