import * as React from 'react';
import { TraceItem } from './TraceSelectorRow';
import Sidebar from './Sidebar';
import Window from './Window';

type Props = {};

export default function App(_: Props): React.ReactElement {
  const [currentTrace, setCurrentTrace] = React.useState<TraceItem | null>(
    null,
  );
  return (
    <div className="flex items-start">
      <Sidebar currentTrace={currentTrace} setCurrentTrace={setCurrentTrace} />
      <Window currentTrace={currentTrace} />
    </div>
  );
}
