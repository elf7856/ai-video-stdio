declare module '@webav/av-canvas' {
  export class AVCanvas {
    constructor(container: HTMLElement, options?: {
      width?: number;
      height?: number;
      bgColor?: string;
    });

    play(options?: { start?: number; end?: number }): Promise<void>;
    pause(): Promise<void>;
    destroy(): Promise<void>;

    addSprite(sprite: any): Promise<void>;
    previewFrame(time: number): Promise<void>;

    on(event: 'timeupdate', handler: (time: number) => void): () => void;
    on(event: 'paused', handler: () => void): () => void;
    on(event: 'playing', handler: () => void): () => void;
    on(event: 'ended', handler: () => void): () => void;

    get volume(): number;
    set volume(value: number);
  }
}

declare module '@webav/av-cliper' {
  export interface IClip {
    ready: Promise<void>;
    tick(time: number): Promise<{ video?: VideoFrame; audio?: Float32Array[] }>;
    destroy(): void;
  }

  export class MP4Clip implements IClip {
    constructor(source: ReadableStream<Uint8Array> | File);
    ready: Promise<void>;
    tick(time: number): Promise<{ video?: VideoFrame; audio?: Float32Array[] }>;
    destroy(): void;

    get duration(): number;
    get width(): number;
    get height(): number;
  }

  export class Combinator {
    constructor(options?: { width?: number; height?: number; videoCodec?: string; audioCodec?: string });

    addSprite(sprite: Sprite): Promise<void>;
    output(): ReadableStream<Uint8Array>;
    destroy(): void;
  }

  export class Sprite {
    constructor(clip: IClip);

    setAnimation(animation: {
      from: { x: number; y: number; w: number; h: number };
      to: { x: number; y: number; w: number; h: number };
    }, options?: { duration?: number; delay?: number }): void;

    time: { offset: number; duration: number };
    rect: { x: number; y: number; w: number; h: number };

    destroy(): void;
  }

  export class VisibleSprite extends Sprite {
    constructor(clip: IClip);
  }

  export class OffscreenSprite extends Sprite {
    constructor(clip: IClip);
  }

  export function renderTxt2ImgBitmap(
    text: string,
    style?: string
  ): Promise<ImageBitmap>;
}
