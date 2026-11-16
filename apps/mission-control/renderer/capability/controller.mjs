import { buildQuery, chooseDossier } from "./model.mjs";

export class DossierController {
  constructor(query, onChange = () => {}) {
    this.query = query;
    this.onChange = onChange;
    this.epoch = 0;
    this.state = { status: "UNKNOWN", dossier: null, records: [], markers: [], cursor: null };
  }
  publish(next) { this.state = { ...this.state, ...next }; this.onChange(this.state); }
  async load(lens, capabilityId, fixture = false) {
    this.epoch += 1;
    this.publish({ lens, capabilityId, fixture, status: "LOADING", dossier: null,
      records: [], markers: [], cursor: null, error: null });
    await this.fetchPage(null, this.epoch);
  }
  async more() {
    if (this.state.cursor && this.state.status !== "LOADING") await this.fetchPage(this.state.cursor, this.epoch);
  }
  async fetchPage(cursor, epoch) {
    const { lens, capabilityId } = this.state;
    this.publish({ status: "LOADING" });
    try {
      const page = await this.query(buildQuery(lens, { cursor }));
      if (epoch !== this.epoch) return;
      const records = [...this.state.records, ...page.records];
      const dossier = chooseDossier(records, lens, capabilityId);
      this.publish({ records, dossier, cursor: page.next_cursor, markers: page.markers,
        coverage: page.coverage, status: !dossier && page.next_cursor ? "PARTIAL" :
          !dossier && page.state === "PRESENT" ? "MISSING" : page.state });
    } catch (error) {
      if (epoch !== this.epoch) return;
      this.publish({ status: "UNAVAILABLE", error: String(error.message), records: [],
        dossier: null, cursor: null, markers: [] });
    }
  }
}
