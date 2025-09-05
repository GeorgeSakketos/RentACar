import cars from "../data/cars";
import CarCard from "../components/CarCard";

export default function Cars() {
  return (
    <section className="cars fade-in">
      <h2>Available Cars</h2>
      <div className="car-list">
        {cars.map((car) => (
          <CarCard key={car.id} car={car} />
        ))}
      </div>
    </section>
  );
}