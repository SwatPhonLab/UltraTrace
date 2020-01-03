import * as React from 'react';
import { AnnotationData } from 'react-image-annotation';
import { SemanticCOLORS } from 'semantic-ui-react';

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

export default function Point({
  annotation,
}: Props): React.ReactElement | null {
  const { geometry } = annotation;
  if (geometry == null) {
    return null;
  }

  return (
    <div
      className="br-100 w1 h1 bg-blue absolute border-box ba bw1 b--white"
      style={{
        top: `${geometry.y}%`,
        left: `${geometry.x}%`,
        transform: 'translate(-50%, -50%)',
      }}
    />
  );
}
