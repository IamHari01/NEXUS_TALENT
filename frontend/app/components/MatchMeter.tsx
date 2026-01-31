export default function MatchMeter({ score }: { score: number }) {
    const color = score > 80 ? "text-green-500" : score > 50 ? "text-yellow-500" : "text-red-500";
    return (
        <div className="flex flex-col items-center">
            <div className={`text-5xl font-bold ${color}`}>{score}%</div>
            <p className="text-gray-500 uppercase text-xs">ATS Shortlist Probability</p>
        </div>
    );
}