export const asyncWorkflow = {
  demo: {
    title: "Demo data received",
    body: [
      "Ribet is building your operational health report now.",
      "This may take a few minutes while we parse the files, normalize the data, and generate findings.",
      "You can leave this page safely. Your report will appear in the dashboard when ready.",
    ],
  },
  upload: {
    title: "Files received",
    body: [
      "Ribet is analyzing your ERP exports now.",
      "You can leave this page safely. Your report will appear in the dashboard when processing is complete.",
    ],
  },
  dashboard: {
    title: "Report in progress",
    body: [
      "Ribet is processing your uploads in the background.",
      "Refresh this page in a few minutes, or check your email if you added a recipient in settings.",
    ],
  },
  consentRequired:
    "Please confirm you have authority to upload this data and accept the Terms and Privacy Policy before uploading.",
} as const;
