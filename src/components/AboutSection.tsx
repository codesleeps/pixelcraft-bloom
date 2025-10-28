import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Trophy, Users, Target, Zap } from "lucide-react";
import { Link } from "react-router-dom";

const achievements = [
  {
    icon: Trophy,
    title: "Award-Winning Agency",
    description: "Recognized as Top Digital Marketing Agency 2023"
  },
  {
    icon: Users,
    title: "Expert Team",
    description: "50+ certified marketing professionals"
  },
  {
    icon: Target,
    title: "Results-Driven",
    description: "Average 300% ROI for our clients"
  },
  {
    icon: Zap,
    title: "Fast Execution",
    description: "Campaign launch within 48 hours"
  }
];

const AboutSection = () => {
  return (
    <section id="about" className="py-24 bg-background">
      <div className="container mx-auto px-4">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Left Content */}
          <div>
            <Badge variant="secondary" className="mb-4 text-primary">About Us</Badge>
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-foreground">
              Your Growth Partner in the 
              <span className="block bg-gradient-primary bg-clip-text text-transparent">Digital Age</span>
            </h2>
            <p className="text-lg text-muted-foreground mb-8 leading-relaxed">
              We're not just another marketing agency. We're growth hackers, data scientists, 
              and creative visionaries who live and breathe digital marketing. Our mission is 
              simple: transform your business into a digital powerhouse.
            </p>
            
            <div className="space-y-4 mb-8">
              <div className="flex items-start gap-3">
                <div className="w-2 h-2 bg-primary rounded-full mt-2" />
                <div>
                  <h4 className="font-semibold mb-1">Data-Driven Approach</h4>
                  <p className="text-muted-foreground">Every decision backed by real data and analytics</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-2 h-2 bg-primary rounded-full mt-2" />
                <div>
                  <h4 className="font-semibold mb-1">Proven Track Record</h4>
                  <p className="text-muted-foreground">500+ successful campaigns across 50+ industries</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-2 h-2 bg-primary rounded-full mt-2" />
                <div>
                  <h4 className="font-semibold mb-1">Full Transparency</h4>
                  <p className="text-muted-foreground">Real-time reporting and complete campaign visibility</p>
                </div>
              </div>
            </div>
            
            <Link to="/partnership">
              <Button variant="hero" size="lg" className="text-lg px-8 py-6 h-auto">
                Partner With Us
              </Button>
            </Link>
          </div>
          
          {/* Right Content - Achievement Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {achievements.map((achievement, index) => {
              const IconComponent = achievement.icon;
              return (
                <Card key={index} className="group hover:shadow-card transition-all duration-300 border-0 bg-gradient-subtle">
                  <CardContent className="p-6 text-center">
                    <div className="w-16 h-16 bg-gradient-primary rounded-full flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform duration-300">
                      <IconComponent className="w-8 h-8 text-white" />
                    </div>
                    <h3 className="font-semibold mb-2">{achievement.title}</h3>
                    <p className="text-sm text-muted-foreground">{achievement.description}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
};

export default AboutSection;
