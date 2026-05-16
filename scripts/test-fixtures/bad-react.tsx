// Fixture: triggers pack-frontend-react rules.
import { useState, useEffect } from "react";

export function BadList({ items }: { items: any[] }) {
  const [list, setList] = useState(items);

  useEffect(() => {
    window.addEventListener("resize", () => console.log("resize"));
    // missing cleanup
  }, []);

  function addItem(item: any) {
    list.push(item);  // direct mutation
    setList(list);
  }

  return (
    <div>
      <img src="/logo.png" />  {/* missing alt */}
      <ul>
        {items.map(it => (
          <li>{it.name}</li>  {/* missing key */}
        ))}
      </ul>
    </div>
  );
}
