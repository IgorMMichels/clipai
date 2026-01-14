import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

interface PreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  url: string | null;
  title?: string;
}

export function PreviewModal({ isOpen, onClose, url, title }: PreviewModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[400px] p-0 overflow-hidden bg-black border-zinc-800">
        <DialogHeader className="sr-only">
          <DialogTitle>Preview: {title || "Clip"}</DialogTitle>
        </DialogHeader>
        {url && (
          <div className="aspect-[9/16] w-full bg-black flex items-center justify-center">
            <video
              src={url}
              controls
              autoPlay
              loop
              className="h-full w-full object-contain"
            />
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
