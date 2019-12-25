import * as React from 'react';

import { List } from 'immutable';
import { Segment, SemanticCOLORS } from 'semantic-ui-react';
import Annotation, {
  AnnotationData,
  HighlightData,
  SelectorType,
} from 'react-image-annotation';
import { PointSelector } from 'react-image-annotation/lib/selectors';
import { identity } from 'ramda';
import image from '../../img/img_grid_square.jpg';
import { TraceItem } from './TraceSelectorRow';
import Point from './Point';

interface Props {
  currentTrace: TraceItem | null;
}

interface TGeometry {
  type: SelectorType;
  x: number;
  y: number;
}

interface TMetadata {
  color: SemanticCOLORS;
}

type MyAnnotationData = AnnotationData<{}, TGeometry, TMetadata>;

/**
 * The main editor window. Provides an interface to annotate a file bundle.
 */
export default function Window({ currentTrace }: Props): React.ReactElement {
  const [annotations, setAnnotations] = React.useState<List<MyAnnotationData>>(
    List(),
  );

  const commitAnnotation = React.useCallback(
    (annotation: MyAnnotationData): void => {
      if (currentTrace == null) {
        return;
      }
      // Add the key `data` with an empty object because we're immediately
      // committing the annotation as they're being added instead of having
      // an intermediate submission step
      setAnnotations(
        annotations.push({
          ...annotation,
          data: { color: currentTrace.color },
        }),
      );
    },
    [currentTrace, annotations],
  );
  function renderHighlight({
    key,
    annotation,
    active,
  }: HighlightData<MyAnnotationData>): React.ReactElement | null {
    const { geometry } = annotation;
    if (geometry == null) {
      return null;
    }

    switch (geometry.type) {
      case PointSelector.TYPE:
        return <Point key={key} annotation={annotation} active={active} />;
      default:
        return null;
    }
  }

  return (
    <Segment>
      <Annotation
        src={image}
        alt=""
        type={PointSelector.TYPE}
        selectors={[PointSelector]}
        annotations={annotations.toArray()}
        value={{}}
        onChange={commitAnnotation}
        onSubmit={identity}
        activeAnnotations={[]}
        renderHighlight={renderHighlight}
        disableEditor
      />
    </Segment>
  );
}
