import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { VideoWithTranscription } from "@/components/ui/video-with-transcription";

interface WordSegment {
  text: string;
  start_time: number;
  end_time: number;
}

interface PreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  url: string | null;
  title?: string;
  transcript?: string;
  wordSegments?: WordSegment[];
}

export function PreviewModal({ isOpen, onClose, url, title, transcript, wordSegments }: PreviewModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[400px] p-0 overflow-hidden bg-black border-zinc-800">
        <DialogHeader className="sr-only">
          <DialogTitle>Preview: {title || "Clip"}</DialogTitle>
        </DialogHeader>
        {url && (
          <div className="aspect-[9/16] w-full">
            <VideoWithTranscription
              videoSrc={url}
              transcript={transcript}
              wordSegments={wordSegments}
              autoPlay={true}
              loop={true}
              controls={true}
            />
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
