declare module '*.jpg';

declare module 'react-image-annotation' {
  import * as React from 'react';

  interface Props<TAnnotation extends AnnotationData = AnnotationData> {
    src: any;
    alt: string;
    annotations: Array<TAnnotation>;
    value: TAnnotation;
    onChange: (annotation: TAnnotation) => void;
    onSubmit: (annotation: TAnnotation) => void;
    type: SelectorType;
    allowTouch: boolean;
    selectors: Array<Selector>;
    activeAnnotations: Array<TAnnotation>;
    activeAnnotationsComparator: (a: TAnnotation, b: TAnnotation) => boolean;
    disableAnnotation: boolean;
    disableSelector: boolean;
    disableEditor: boolean;
    disableOverlay: boolean;
    renderSelector: (
      data: SelectorData<TAnnotation>,
    ) => React.ReactElement | null;
    renderEditor: (data: EditorData<TAnnotation>) => React.ReactElement;
    renderHighlight: (
      data: HighlightData<TAnnotation>,
    ) => React.ReactElement | null;
    renderContent: (data: ContentData<TAnnotation>) => React.ReactElement;
    renderOverlay: (data: OverlayData<TAnnotation>) => React.ReactElement;
  }

  interface SelectorData<T extends AnnotationData> {
    annotation: T;
  }

  interface EditorData<T extends AnnotationData> {
    annotation: T;
    onChange: (annotation: T) => void;
    // TODO: should match the interface of onClick for a div
    onSubmit: (e: React.MouseEvent) => void;
  }

  interface HighlightData<T extends AnnotationData> {
    key: string;
    annotation: T;
    active: boolean;
  }

  interface ContentData<T extends AnnotationData> {
    key: string;
    annotation: T;
  }

  interface OverlayData<T extends AnnotationData> {
    type: SelectorType;
    annotation: T;
  }

  interface Selector {}
  interface SelectorType {}
  export interface AnnotationData<
    TSelection = {},
    TGeometry = { type: SelectorType },
    TMetadata = {}
  > {
    selection?: TSelection;
    geometry?: TGeometry;
    data?: TMetadata;
  }

  // eslint-disable-next-line
  export default class Annotation extends React.Component<Props> {
    // eslint-disable-next-line
    static defaultProps: Pick<
      Props,
      | 'type'
      | 'allowTouch'
      | 'selectors'
      | 'activeAnnotationsComparator'
      | 'disableAnnotation'
      | 'disableSelector'
      | 'disableEditor'
      | 'disableOverlay'
      | 'renderSelector'
      | 'renderEditor'
      | 'renderHighlight'
      | 'renderContent'
      | 'renderOverlay'
    >;
  }
}

declare module 'react-image-annotation/lib/selectors';
