# Development Notes

## MVP Flow

1. User starts the floating window.
2. User selects or configures a screen region.
3. The app captures that region on a timer.
4. OCR extracts text blocks.
5. Visual rules detect unread markers.
6. Parsed candidate cards appear in the floating window.

## Module Boundaries

- `capture`: screen and monitor handling.
- `recognition`: OCR, visual detection, parsing, pipeline.
- `ui`: floating window and future region selector.
- `storage`: local config and future history storage.
- `models`: pydantic models shared across layers.

