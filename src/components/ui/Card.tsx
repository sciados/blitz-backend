"use client";
import React from "react";

export default function Card({
  children,
  className = "",
  elevated = false,
}: {
  children: React.ReactNode;
  className?: string;
  elevated?: boolean;
}) {
  const classes = `card ${elevated ? "card--elevated" : ""} ${className}`;
  return <div className={classes}>{children}</div>;
}
