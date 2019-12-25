import * as React from 'react';

import { OrderedMap } from 'immutable';
import { CheckboxProps, Segment } from 'semantic-ui-react';

import TraceSelectorRow, { TraceItem } from './TraceSelectorRow';

import PlaybackControls from './PlaybackControls';
import SeekableSelector from './SeekableSelector';
import TraceSelector from './TraceSelector';

interface Props {
  currentTrace: TraceItem | null;
  setCurrentTrace: (item: TraceItem | null) => void;
}

/**
 * The application sidebar. Provides an interface to select frames, modify
 * traces, and control playback.
 */
export default function Sidebar({
  currentTrace,
  setCurrentTrace,
}: Props): React.ReactElement {
  const [traces, setTraces] = React.useState<OrderedMap<string, TraceItem>>(
    OrderedMap(),
  );
  const upsertTrace = React.useCallback(
    (item: TraceItem) => setTraces(traces.set(item.id, item)),
    [traces],
  );
  const lookupTraceByKeyAndSetCurrent = React.useCallback(
    (data: CheckboxProps) => {
      const { value } = data;
      if (value == null || typeof value === 'number') {
        throw new Error(`Expected a string but got '${value}'`);
      }
      setCurrentTrace(traces.get(value, null));
    },
    [traces],
  );

  const traceElements = traces
    .map((item: TraceItem) => (
      <TraceSelectorRow
        key={item.id}
        item={item}
        onEditItem={upsertTrace}
        isSelected={currentTrace?.id === item.id}
        onSelect={lookupTraceByKeyAndSetCurrent}
      />
    ))
    .valueSeq();
  return (
    <Segment>
      <SeekableSelector placeholder="Bundle..." />
      <SeekableSelector placeholder="Frame..." />
      <TraceSelector traces={traceElements} onAddTrace={upsertTrace} />
      <PlaybackControls />
    </Segment>
  );
}
