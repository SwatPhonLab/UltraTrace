import * as React from 'react';

import { AnnotationData } from 'react-image-annotation';
import { SemanticCOLORS } from 'semantic-ui-react';
import styled from 'styled-components';

interface Props {
  annotation: AnnotationData<{}, HasXY, HasColor>;
  active: boolean;
}

interface HasColor {
  color: SemanticCOLORS;
}

interface HasXY {
  x: number;
  y: number;
}

// prettier-ignore
const Container = styled.div`
  border: solid 3px white;
  border-radius: 50%;
  box-sizing: border-box;
  box-shadow:
    0 0 0 1px rgba(0,0,0,0.3),
    0 0 0 2px rgba(0,0,0,0.2),
    0 5px 4px rgba(0,0,0,0.4);
  height: 16px;
  position: absolute;
  transform: translate3d(-50%, -50%, 0);
  width: 16px;
`

export default function Point({
  annotation,
}: Props): React.ReactElement | null {
  const { geometry } = annotation;
  if (geometry == null) {
    return null;
  }

  return (
    <Container
      style={{
        top: `${geometry.y}%`,
        left: `${geometry.x}%`,
        'background-color': annotation.data?.color,
      }}
    />
  );
}
