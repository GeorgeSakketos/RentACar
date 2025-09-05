export default function CarCard({ car }) {
  return (
    <div className="car-card fade-in">
      <img src={car.image} alt={car.name} />
      <h3>{car.name}</h3>
      <p>${car.price}/day</p>
      <button className="btn">Book Now</button>
    </div>
  );
}